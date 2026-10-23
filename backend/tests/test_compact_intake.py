import json
from datetime import datetime
import pytest
from test_slm_intake import Provider
from app.services.nlp import slm_extractor as intake
from app.services.nlp.compact_intake import expand_response, wire_schema


def test_wire_budget_and_core_absence_are_explicit(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    provider=Provider(raw=json.dumps({'facts':{'speed':['150'],'state':['andhra pradesh'],
        'date':['yesturday'],'road_type':['highway'],'vehicle':[]}}))
    e,m=intake.interpret('150 highway yesturday andhra pradesh',
        datetime.fromisoformat('2026-10-23T09:00:00+05:30'),provider=provider)
    assert next(x for x in e if x['type']=='OBSERVED_SPEED')['normalizedValue']=='150'
    assert next(x for x in e if x['type']=='EVENT_DATE')['normalizedValue']=='2026-10-22'
    assert not any(x['type']=='VEHICLE_CLASS' for x in e)
    assert provider.calls[0][2]['max_tokens']==640
    schema=provider.calls[0][2]['output_schema']
    assert set(schema['properties']['facts']['required'])=={'speed','state','date','vehicle','road_type'}
    assert not m['fallbackUsed']


def test_compact_retains_conflicting_numbers_and_context():
    data=expand_response(json.dumps({'facts':{'speed':['120 or 140'],'location':['school zone']}}))
    assert [f['value'] for f in data['facts'][:2]]==['120','140']
    assert all(f['certainty']=='ambiguous' for f in data['facts'][:2])


@pytest.mark.parametrize('raw',['{"facts":{"speed":"150"}}','{"facts":{"speed":[150]}}',
    '{"facts":{},"charges":"guilty"}'])
def test_compact_invalid_structure_fails(raw):
    with pytest.raises(ValueError):expand_response(raw)


def test_invented_quote_does_not_become_a_fact(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    provider=Provider(raw=json.dumps({'facts':{'speed':['150'],'vehicle':['truck'],
        'speed_unit':['in'],'date':[],'state':[],'road_type':[]}}))
    e,m=intake.interpret('150 in highway',provider=provider)
    assert not any(x['type'] in {'VEHICLE_CLASS','OBSERVED_SPEED_UNIT'} for x in e)
    assert len(m['rejectedMentions'])==2
