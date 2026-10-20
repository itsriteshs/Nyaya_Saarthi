import json
import pytest
from app.services.nlp.entity_extractor import extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.slot_detector import detect_slots
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.output_checks import check_language
from app.services.llm.response_parser import parse_response
from app.services.llm.grounding_validator import validate
from test_llm_phase5 import output, package


def test_explicit_facts_are_scoped_and_do_not_reask():
    entities=[normalize(e) for e in extract('Your role: witness; RC status: cancelled; injury status: no; death status: unknown',status_values={})]
    found={e['type']:e for e in entities}
    assert found['USER_ROLE']['normalizedValue']=='witness'
    assert found['RC_STATUS']['normalizedValue']=='cancelled'
    assert found['INJURY_PRESENT']['normalizedValue']=='no'
    assert found['DEATH_PRESENT']['status']=='unresolved'
    assert 'USER_ROLE' not in {s['slot'] for s in detect_slots('INT003',entities)['missingSlots']}
    assert not [e for e in extract('Is an owner responsible for injury?',status_values={}) if e['type'] in {'USER_ROLE','INJURY_PRESENT'}]


def test_schema_conditions_are_explicit_not_assumed():
    entities=[{'type':'LOCATION','normalizedValue':'a junction','status':'resolved'}]
    assert not any(s['slot']=='LOCATION' for s in detect_slots('INT002',entities)['unresolvedSlots'])
    assert any(s['slot']=='LOCATION' for s in detect_slots('INT002',[],required_slots={'LOCATION'})['missingSlots'])
    assert not any(s['slot']=='LOCATION' for s in detect_slots('INT002',[])['missingSlots'])


def test_status_negation_and_date_label_do_not_make_false_facts():
    entities=[normalize(e) for e in extract('I received a challan. Date: 2026-07-09. Please explain.',status_values={})]
    assert any(e['type']=='CHALLAN_STATUS' and e['normalizedValue']=='issued' for e in entities)
    assert all(e['status']=='resolved' for e in entities if e['type']=='EVENT_DATE')
    entity={'type':'LICENCE_STATUS','text':'invalid','value':'invalid','method':'rule'}
    assert normalize(entity)['normalizedValue']=='absent'


def test_explicit_destination_and_specialized_dates_keep_their_slots():
    entities=[normalize(e) for e in extract('Destination state: Kerala; Licence expiry date: 2027-03-21',status_values={})]
    values={e['type']:e['normalizedValue'] for e in entities if e['status']=='resolved'}
    assert values['DESTINATION_STATE']=='Kerala'
    assert values['LICENCE_EXPIRY_DATE']=='2027-03-21'


def test_structured_adapter_and_truncation(monkeypatch):
    provider=OllamaProvider('http://127.0.0.1:11434');calls=[]
    def request(path,payload,timeout):
        calls.append(payload)
        return {'message':{'content':'{}'},'done_reason':'stop'}
    monkeypatch.setattr(provider,'_request',request)
    provider.generate('test',[],temperature=0,max_tokens=700,timeout=2)
    assert set(calls[0]['format']['required'])==set(output())
    assert calls[0]['options']['seed']==471
    from app.services.llm.prompt_builder import response_schema
    schema=response_schema(package(),'hindi')
    assert schema['properties']['language']['enum']==['hindi']
    assert schema['properties']['recommendedActions']['maxItems']==0
    assert schema['$defs']['LegalClaim']['properties']['evidenceIds']['items']['enum']==['EVID:PROV_MVA_S112']
    monkeypatch.setattr(provider,'_request',lambda *a,**kw:{'done_reason':'length'})
    with pytest.raises(RuntimeFailure,match='OUTPUT_TRUNCATED'):
        provider.generate('test',[],temperature=0,max_tokens=700,timeout=2)


def test_schema_and_language_fail_closed():
    with pytest.raises(ValueError,match='OUTPUT_SCHEMA_INVALID'):
        parse_response(json.dumps(output())[:-1]+',"answer":"replacement"}')
    for language in ('hindi','hinglish'):
        with pytest.raises(ValueError,match='OUTPUT_LANGUAGE_MISMATCH'):
            check_language(parse_response(json.dumps(output(language=language))),language)
    verdict=validate(parse_response(json.dumps(output(uncertainties=[]))),package())
    assert 'OMITTED_UNCERTAINTY' in verdict['reasonCodes']
    # No outcome, numeric, ID, or literal-linkage check was relaxed.
    for changes,reason in [({'answer':'You must pay a fine of 900 rupees.'},'UNSUPPORTED_PENALTY'),
                           ({'answer':'You violated the law.'},'DEFINITE_OUTCOME'),
                           ({'legalClaims':[{'text':'Invented','evidenceIds':['fake']}]},'UNKNOWN_EVIDENCE_ID')]:
        assert reason in validate(parse_response(json.dumps(output(**changes))),package())['reasonCodes']


def test_known_server_uncertainty_does_not_assert_an_outcome():
    evidence=package(); evidence['uncertainties']=['No speed threshold or penalty is asserted.']
    safe=parse_response(json.dumps(output(uncertainties=evidence['uncertainties'])))
    assert validate(safe,evidence)['accepted']
    for field in ('answer','explanation'):
        bad=parse_response(json.dumps(output(**{field:'You violated the law.'},uncertainties=evidence['uncertainties'])))
        assert 'DEFINITE_OUTCOME' in validate(bad,evidence)['reasonCodes']
    bad=parse_response(json.dumps(output(uncertainties=['The penalty is payable.'])))
    assert 'DEFINITE_OUTCOME' in validate(bad,evidence)['reasonCodes']
