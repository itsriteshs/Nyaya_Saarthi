from workflow_helpers import establish_issue
from uuid import uuid4
import pytest
from app.services.legal.knowledge import load_knowledge
from app.services.legal.policy import provision_policy, source_policy
from app.services.legal.guidance import readiness
from app.services.legal import index
from app.services.legal.rules import evaluate_rule


@pytest.fixture
def lexical_index(tmp_path, monkeypatch):
    monkeypatch.setattr(index,'INDEX_DIR',tmp_path/'legal_index')
    index.load_index.cache_clear()
    manifest=index.build(semantic=False)
    yield manifest
    index.load_index.cache_clear()


def test_source_policy_and_dataset_gaps():
    knowledge=load_knowledge()
    assert source_policy(knowledge['tables']['sources']['SRC_MVA_1988'],knowledge)['status']=='eligible'
    assert provision_policy(knowledge['tables']['provisions']['PROV_MVA_S112'],knowledge)['status']=='eligible'
    assert provision_policy(knowledge['tables']['provisions']['PROV_MVA_S112'],knowledge,'1980-01-01','JX_IN_CENTRAL')['status']=='excluded'
    report=readiness()
    assert report['sources']['eligible']==6
    assert report['provisions']['eligible']==4
    assert report['procedures']['eligible']==0
    assert not any(item['file']=='procedures.csv' and item['row']==26 for item in report['malformedRecords'])
    repaired=knowledge['tables']['procedures']['PROC_CONTEST_ECHALLAN_COURT']
    assert repaired['source_id']=='SRC_MVAA_2019'
    assert repaired['review_status']=='NOT_VERIFIED'
    from app.services.legal.guidance import procedure_policy
    assert procedure_policy(repaired,knowledge)['status']=='excluded'


def test_retrieval_requires_date_and_jurisdiction(lexical_index):
    assert lexical_index['retrievalMode']=='lexical-only'
    limited=index.retrieve('speed limit',None,None)
    assert limited['results']==[]
    result=index.retrieve('speed limit','2026-10-19','JX_IN_CENTRAL')
    assert any(item['recordId']=='PROV_MVA_S112' for item in result['results'])
    assert all(item['admissibility']=='eligible' for item in result['results'])


def test_rule_engine_uses_confirmed_facts_and_abstains_on_speed_lookup():
    knowledge=load_knowledge();rules=knowledge['tables']['rules']
    def fact(key,value,normalized_id=None):
        return {'id':'fact-'+key,'key':key,'label':key,'value':value,'normalizedValue':value,
                'normalizedId':normalized_id,'provenance':'USER_CONFIRMED','confirmed':True}
    matter={'facts':[fact('STATE','Tamil Nadu','JX_IN_TN'),fact('EVENT_DATE','2026-10-19'),
                     fact('VEHICLE_CLASS','car','VC_MOTORCAR'),fact('INSURANCE_STATUS','expired'),
                     fact('ROAD_TYPE','expressway'),fact('OBSERVED_SPEED','120')]}
    insurance=evaluate_rule(rules['RULE_INSURANCE_REQUIRED_GENERAL'],matter,knowledge)
    assert insurance['status']=='MATCHED'
    assert insurance['matchedFactIds']==['fact-INSURANCE_STATUS']
    speed=evaluate_rule(rules['RULE_SPEED_LMV_LIMIT_CHECK'],matter,knowledge)
    assert speed['status']=='INSUFFICIENT_CONTEXT'
    assert 'SPEED_LIMIT_REVIEW_MISSING' in speed['reasons']
    assert 'VEHICLE_CLASS_SCOPE_UNPROVEN' in speed['reasons']
    matter['facts'][3]['confirmed']=False
    assert evaluate_rule(rules['RULE_INSURANCE_REQUIRED_GENERAL'],matter,knowledge)['status']=='INSUFFICIENT_CONTEXT'


def test_verified_guidance_persists_and_fact_edit_invalidates(client,lexical_index):
    created=client.post('/api/v1/matters',json={'originalText':'I drove my car at 120 km/h on an expressway in Kerala on 2026-10-19','language':'english'}).json()
    url=f"/api/v1/matters/{created['id']}"
    assert client.post(url+'/guidance',json={'revision':created['revision']}).status_code==409
    analyzed=client.post(url+'/analyze',json={'revision':created['revision']}).json()
    matter=establish_issue(client,url,analyzed)
    for fact in list(matter['facts']):
        reply=client.post(url+'/facts/'+fact['id']+'/confirm',json={'revision':matter['revision']})
        assert reply.status_code==200,reply.text
        matter=reply.json()
    reply=client.post(url+'/verify',json={'revision':matter['revision'],'acknowledgeUnknowns':True})
    assert reply.status_code==200,reply.text
    matter=reply.json()
    status=client.get('/api/v1/legal/status')
    assert status.status_code==200
    assert status.json()['index']['retrievalMode']=='lexical-only'
    diagnostic=client.post('/api/v1/legal/retrieve',json={'matterId':matter['id'],'revision':matter['revision']})
    assert diagnostic.status_code==200,diagnostic.text
    assert diagnostic.json()['retrievalMode']=='lexical-only'
    generated=client.post(url+'/guidance',json={'revision':matter['revision']})
    assert generated.status_code==200,generated.text
    matter=generated.json()
    assert matter['stage']=='GUIDANCE_GENERATED'
    guidance=matter['guidance']
    assert guidance['metadata']['retrievalMode']=='lexical-only'
    assert 'speed threshold or penalty' in ' '.join(guidance['uncertainties'])
    assert client.get(url).json()['guidance']==guidance
    assert client.post(url+'/guidance',json={'revision':matter['revision']}).status_code==409
    assert client.post(url+'/complete',json={'revision':matter['revision']-1}).status_code==409
    completed=client.post(url+'/complete',json={'revision':matter['revision']})
    assert completed.status_code==200,completed.text
    matter=completed.json()
    assert matter['stage']=='COMPLETED'
    fact=next(f for f in matter['facts'] if f['key']=='OBSERVED_SPEED')
    edited=client.patch(url+'/facts/'+fact['id'],json={'revision':matter['revision'],'value':'90 km/h'})
    assert edited.status_code==200,edited.text
    assert edited.json().get('guidance') is None
    assert edited.json()['stage']!='COMPLETED'
