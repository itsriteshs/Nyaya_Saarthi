import json
import pytest
from test_slm_intake import Provider, mention, send
from test_llm_phase5 import output, package
from app.services.nlp import slm_extractor as intake
from app.services.llm.response_parser import parse_response
from app.services.llm.grounding_validator import validate


@pytest.mark.parametrize('text,slot,normalized', [('Main road','ROAD_TYPE','other'),('In a school zone','LOCATION','school zone')])
def test_context_survives(text, slot, normalized):
    facts=[mention(slot,text, 'school zone' if slot=='LOCATION' else text)]
    entities=intake.validate_mentions(json.dumps({'facts':facts}),text)
    assert entities[0]['normalizedValue']==normalized
    assert entities[0]['text']==text and entities[0]['status']=='resolved'


def test_missing_unit_and_conflicting_speed(client,monkeypatch):
    monkeypatch.setenv('NYAYA_ASSUME_INDIAN_SPEED_KMPH','false')
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    provider=Provider([mention('OBSERVED_SPEED','doing 120','120')])
    monkeypatch.setattr(intake,'OllamaProvider',lambda url:provider)
    m=client.post('/api/v1/matters',json={'originalText':'I was doing 120. Can I be fined?','language':'english'}).json()
    url='/api/v1/matters/'+m['id'];m=client.post(url+'/analyze',json={'revision':m['revision']}).json()
    f=m['facts'][0];assert f['normalizedValue']=='120' and f['unit']=='unknown' and f['resolutionStatus']=='unresolved'
    if m['currentQuestion']['slot']=='INTENT':m=send(client,url,m,'INT002')
    # Directly exercise the persisted planner when speed is the active question.
    from app.services import conversation
    context=m.copy();context['currentQuestion']=conversation._question(context,'OBSERVED_SPEED')
    assert 'unit' in context['currentQuestion']['question']
    provider.facts=[]
    conversation.apply_answer(context,'km/h',context['currentQuestion']['id'],'unit-reply')
    speed=next(f for f in context['facts'] if f['key']=='OBSERVED_SPEED')
    assert speed['unit']=='km/h' and speed['normalizedValue']=='120'
    context['currentQuestion']=conversation._question(context,'OBSERVED_SPEED')
    provider.facts=[mention('OBSERVED_SPEED','140kmph','140')]
    conversation.apply_answer(context,'140kmph',context['currentQuestion']['id'],'conflict-reply')
    assert context['conversation']['contradictions'][-1]['previous']['normalizedValue']=='120'
    assert context['conversation']['contradictions'][-1]['candidate']['normalizedValue']=='140'
    assert not context['conversation']['contradictions'][-1]['resolved']


def test_attributed_speed_is_not_a_legal_threshold():
    p=package();p['facts']=[{'key':'OBSERVED_SPEED','value':'120','unit':'km/h'}]
    o=output(answer='You reported a speed of 120 km/h. Section 112 may be relevant.')
    assert validate(parse_response(json.dumps(o)),p)['accepted']
    for text in ['The legal limit is 120 km/h.','You reported a speed of 130 km/h.',
                 'You reported a speed of 120 km/h. The limit is 120 km/h.']:
        o=output(answer=text)
        assert 'UNSUPPORTED_SPEED_FIGURE' in validate(parse_response(json.dumps(o)),p)['reasonCodes']
    p['facts'][0]['unit']='unknown'
    assert not validate(parse_response(json.dumps(output(answer='You reported a speed of 120 km/h.'))),p)['accepted']


@pytest.mark.parametrize('changes,reason',[
    ({'legalClaims':[{'text':'Different wording','evidenceIds':['EVID:PROV_MVA_S112']}]},'UNLINKED_CLAIM'),
    ({'legalClaims':[{'text':'Section 112 may be relevant.','evidenceIds':['fake']}]},'UNKNOWN_EVIDENCE_ID'),
    ({'answer':'Section 999 applies.'},'UNKNOWN_SECTION'),
    ({'answer':'You will be fined.'},'DEFINITE_OUTCOME'),
    ({'answer':'The fine is ₹500.'},'UNSUPPORTED_PENALTY'),
    ({'answer':'Respond in 14 days.'},'UNSUPPORTED_DEADLINE'),
    ({'uncertainties':[]},'OMITTED_UNCERTAINTY'),
])
def test_grounding_gates_retained(changes,reason):
    assert reason in validate(parse_response(json.dumps(output(**changes))),package())['reasonCodes']


def test_road_context_answer_completes_without_rejection(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('LOCATION','In a school zone','school zone')])
    entities,meta=intake.interpret('In a school zone',provider=p,target_slot='ROAD_TYPE')
    assert not meta['fallbackUsed']
    assert any(e['type']=='LOCATION' and e['normalizedValue']=='school zone' for e in entities)
    assert any(e['type']=='ROAD_TYPE' and e['normalizedValue']=='other' for e in entities)


def test_short_answer_schema_prevents_canonical_invention(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('ROAD_TYPE','Main road')])
    intake.interpret('Main road',provider=p,target_slot='ROAD_TYPE')
    props=p.calls[0][2]['output_schema']['properties']['facts']['properties']
    assert props['road_type']['items']['type']=='string'
    assert 'value' not in props


def test_no_evidence_never_calls_model(monkeypatch):
    from app.services.llm import explanation_service as service
    baseline={'sources':[], 'metadata':{'indexVersion':'test','sourceFingerprint':'test'},
              'nextSteps':[], 'uncertainties':['No eligible source supports a conclusion.']}
    monkeypatch.setattr(service,'deterministic_generate',lambda matter:baseline)
    provider=Provider()
    result=service.generate_explanation({'id':'test','facts':[],'intent':{'label':'Speed'}},'llama3.2-3b','english',provider)
    assert not provider.calls
    assert result['metadata']['failureReason']=='INSUFFICIENT_ELIGIBLE_EVIDENCE'


def test_other_road_keeps_separate_context(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('ROAD_TYPE','In a school zone')])
    entities,meta=intake.interpret('In a school zone',provider=p,target_slot='ROAD_TYPE')
    assert not meta['fallbackUsed']
    assert any(e['type']=='LOCATION' and e['normalizedValue']=='In a school zone' for e in entities)
