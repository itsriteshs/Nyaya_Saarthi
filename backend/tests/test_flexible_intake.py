import json
from datetime import datetime
from uuid import uuid4
import pytest
from test_slm_intake import mention, Provider
from app.services.nlp import slm_extractor as intake
from app.services.nlp.flexible_normalization import state_candidate


@pytest.mark.parametrize('word',['andrapradesh','AndhraPradesh','Andhra Prdesh','tamilnadu'])
def test_general_state_normalization(word):
    candidate=state_candidate(word)
    assert candidate and candidate['state_ut_name'] in {'Andhra Pradesh','Tamil Nadu'}


@pytest.mark.parametrize('word',['Pradesh','India','somewhere','Atlantis'])
def test_ambiguous_or_unknown_state_not_guessed(word):
    assert state_candidate(word) is None


def test_assumptions_and_relative_date_are_visible(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    monkeypatch.setattr(intake,'current_reference',lambda:datetime.fromisoformat('2026-10-22T00:01:00+05:30'))
    facts=[mention('STATE','andrapradesh'),mention('OBSERVED_SPEED','150'),mention('EVENT_DATE','today',certainty='uncertain')]
    entities,meta=intake.interpret('150 andrapradesh today',provider=Provider(facts))
    speed=next(e for e in entities if e['type']=='OBSERVED_SPEED')
    assert speed['normalizedValue']=='150' and speed['unit']=='km/h'
    assert speed['unitSource']=='context_default' and speed['interpretationNotes']
    assert next(e for e in entities if e['type']=='STATE')['normalizedValue']=='Andhra Pradesh'
    date=next(e for e in entities if e['type']=='EVENT_DATE')
    assert date['normalizedValue']=='2026-10-22' and date['status']=='resolved'
    assert meta['modelCalled'] and not meta['fallbackUsed']


def test_context_spans_not_false_conflicts_and_verification_required(client,monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('LOCATION','highway'),mention('LOCATION','andrapradesh'),
                mention('STATE','andrapradesh'),mention('OBSERVED_SPEED','150')])
    monkeypatch.setattr(intake,'OllamaProvider',lambda url:p)
    m=client.post('/api/v1/matters',json={'originalText':'150 highway andrapradesh','language':'english'}).json()
    url='/api/v1/matters/'+m['id'];m=client.post(url+'/analyze',json={'revision':m['revision']}).json()
    assert not m['conversation']['contradictions']
    assert len([f for f in m['facts'] if f['key']=='LOCATION'])==2
    assert next(f for f in m['facts'] if f['key']=='OBSERVED_SPEED')['interpretationNotes']
    if m['currentQuestion']['slot']=='INTENT':
        m=client.post(url+'/answers',json={'revision':m['revision'],'questionId':m['currentQuestion']['id'],
            'messageId':str(uuid4()),'answer':'INT002'}).json()
    assert m['currentQuestion']['slot'] not in {'STATE','OBSERVED_SPEED','LOCATION'}
    assert client.post(url+'/verify',json={'revision':m['revision']}).status_code==409


def test_unit_reply_is_slm_interpreted_with_context(client,monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('OBSERVED_SPEED','150')])
    monkeypatch.setattr(intake,'OllamaProvider',lambda url:p)
    m=client.post('/api/v1/matters',json={'originalText':'150 speed','language':'english'}).json()
    m=client.post('/api/v1/matters/'+m['id']+'/analyze',json={'revision':m['revision']}).json()
    from app.services import conversation
    m['currentQuestion']=conversation._question(m,'OBSERVED_SPEED')
    # Also accepts a model incorrectly placing a unit-only value in the speed slot.
    p.facts=[mention('OBSERVED_SPEED','km/h')]
    conversation.apply_answer(m,'km/h',m['currentQuestion']['id'],'unit-message')
    speed=next(f for f in m['facts'] if f['key']=='OBSERVED_SPEED')
    assert speed['normalizedValue']=='150' and speed['unitSource']=='user_provided'
    assert not speed['interpretationNotes']
    assert 'conversationContext' in p.calls[-1][1][-1]['content']


def test_one_bad_mention_does_not_erase_valid_facts(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    p=Provider([mention('VEHICLE_CLASS','car'),mention('STATE','Atlantis')])
    entities,meta=intake.interpret('my car',provider=p)
    assert entities[0]['type']=='VEHICLE_CLASS' and meta['rejectedMentions']


def test_stated_mph_never_defaults_to_kmph():
    e=intake.validate_mentions(json.dumps({'facts':[mention('OBSERVED_SPEED','150 mph','150')]}),'150 mph')[0]
    assert e['unit']=='mph' and e['status']=='unresolved'


def test_model_unit_uncertainty_does_not_reject_literal_unit(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED','true')
    e,m=intake.interpret('km/h',provider=Provider([mention('OBSERVED_SPEED_UNIT','km/h',certainty='uncertain')]),target_slot='OBSERVED_SPEED')
    assert e[0]['unit']=='km/h' and e[0]['status']=='resolved'


def test_assumed_unit_skips_repeat_but_hypothetical_stays_open():
    payload=lambda quote:json.dumps({'facts':[mention('OBSERVED_SPEED',quote,'150',certainty='uncertain')]})
    e=intake.validate_mentions(payload('150'),'150')[0]
    assert e['status']=='resolved' and e['interpretationNotes']
    e=intake.validate_mentions(payload('maybe 150'),'maybe 150')[0]
    assert e['status']=='unresolved'
