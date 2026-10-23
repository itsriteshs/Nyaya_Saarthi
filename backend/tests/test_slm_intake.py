"""Contract/integration tests use a simulated provider, not real model scores."""
import json
from datetime import datetime
from uuid import uuid4

import pytest
from app.services.llm.provider import Generation
from app.services.llm.local_runtime import RuntimeFailure
from app.services.nlp import slm_extractor as intake


def mention(slot, quote, value=None, certainty='clear', approximate=False):
    return dict(slot=slot, quote=quote, value=value or quote, certainty=certainty, approximate=approximate)


class Provider:
    def __init__(self, facts=None, error=None, raw=None):
        self.facts = facts or []
        self.error = error
        self.raw = raw
        self.calls = []

    def availability(self):
        return {'models': {k: {'available': True} for k in intake.MODELS}}

    def generate(self, name, messages, **kwargs):
        self.calls.append((name, messages, kwargs))
        if self.error:
            raise RuntimeFailure(self.error)
        return Generation(self.raw if self.raw is not None else json.dumps({'facts': self.facts}), 2)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv('NYAYA_INTAKE_SLM_ENABLED', 'true')
    monkeypatch.setenv('NYAYA_INTAKE_MODEL', 'llama3.2-3b')


EXAMPLE = 'I was driving in a car at around 130 km/h in a school zone, and was caught by the police. What charges will I face?'
FACTS = [mention('VEHICLE_CLASS', 'car'), mention('OBSERVED_SPEED', 'around 130 km/h', '130', approximate=True),
         mention('LOCATION', 'school zone'), mention('POLICE_INVOLVEMENT', 'caught by the police')]


def test_primary_model_call_and_schema(enabled):
    provider = Provider(FACTS)
    entities, meta = intake.interpret(EXAMPLE, provider=provider)
    assert not meta['fallbackUsed'] and meta['modelCalled']
    assert provider.calls[0][0] == 'llama3.2:3b-instruct-q4_K_M'
    assert EXAMPLE in provider.calls[0][1][1]['content']
    assert provider.calls[0][2]['output_schema']['additionalProperties'] is False
    assert {e['type'] for e in entities} == {f['slot'] for f in FACTS}
    speed = next(e for e in entities if e['type'] == 'OBSERVED_SPEED')
    assert speed['normalizedValue'] == '130' and speed['approximate']
    assert not any(e['type'] in {'CHALLAN_STATUS', 'POLICE_REPORTED'} for e in entities)


@pytest.mark.parametrize('text,facts', [
    ('Police stopped my car beside a school; I clocked 135 km/h.', [mention('VEHICLE_CLASS', 'car'), mention('LOCATION', 'beside a school'), mention('OBSERVED_SPEED', '135 km/h', '135')]),
    ('मेरी कार स्कूल के पास लगभग 130 किलोमीटर प्रति घंटा चल रही थी।', [mention('VEHICLE_CLASS', 'कार'), mention('LOCATION', 'स्कूल के पास'), mention('OBSERVED_SPEED', 'लगभग 130 किलोमीटर प्रति घंटा', '130', approximate=True)]),
    ('Meri car school ke paas 125kmph thi, police ne roka.', [mention('VEHICLE_CLASS', 'car'), mention('LOCATION', 'school ke paas'), mention('OBSERVED_SPEED', '125kmph', '125'), mention('POLICE_INVOLVEMENT', 'police ne roka')]),
])
def test_paraphrases_without_phrase_rules(enabled, text, facts):
    entities, meta = intake.interpret(text, provider=Provider(facts))
    assert not meta['fallbackUsed']
    assert len(entities) == len(facts)
    assert all(e['text'] in text for e in entities)


@pytest.mark.parametrize('value,reference,expected', [
    ('2026-10-21', None, '2026-10-21'), ('21/10/2026', None, '2026-10-21'),
    ('21 October 2026', None, '2026-10-21'), ('03/04/2026', None, None),
    ('yesterday', '2026-10-22T12:00:00+05:30', '2026-10-21'),
    ('आज', '2026-10-22T12:00:00+05:30', '2026-10-22'),
    ('beeta kal', '2026-10-22T12:00:00+05:30', '2026-10-21'),
    ('kal', '2026-10-22T12:00:00+05:30', None), ('yesterday', None, None),
    ('yesterday', '2026-10-22T12:00:00', None),
])
def test_dates(enabled, value, reference, expected):
    reference = datetime.fromisoformat(reference) if reference else None
    entities, _ = intake.interpret(value, reference, provider=Provider([mention('EVENT_DATE', value)]))
    assert entities[0]['normalizedValue'] == expected
    assert entities[0]['status'] == ('resolved' if expected else 'unresolved')


@pytest.mark.parametrize('raw', ['not json', '{"facts":[],"charges":"speeding"}',
    json.dumps({'facts': [mention('FINE', 'car')]}),
    json.dumps({'facts': [mention('VEHICLE_CLASS', 'truck')]}),
    json.dumps({'facts': [mention('OBSERVED_SPEED', 'car', '150')]}),
    json.dumps({'facts': [{**mention('VEHICLE_CLASS', 'car'), 'confirmed': True}]}),
    '{"facts":[]}'])
def test_invalid_output_falls_back(enabled, raw):
    entities, meta = intake.interpret('my car at 150kmph', provider=Provider(raw=raw))
    assert meta['fallbackUsed'] and meta['failureReason']
    assert any(e['type'] == 'OBSERVED_SPEED' and e['normalizedValue'] == '150' for e in entities)


@pytest.mark.parametrize('error', ['INFERENCE_TIMEOUT', 'RUNTIME_UNREACHABLE', 'OUTPUT_TRUNCATED'])
def test_runtime_errors(enabled, error):
    entities, meta = intake.interpret('my car', provider=Provider(error=error))
    assert entities and meta['failureReason'] == error and meta['fallbackUsed']


def test_unavailable_does_not_invoke_generation(enabled):
    p = Provider()
    p.availability = lambda: {'models': {'llama3.2-3b': {'available': False, 'status': 'not_installed'}}}
    _, meta = intake.interpret('car', provider=p)
    assert not p.calls and not meta['modelCalled'] and meta['failureReason'] == 'NOT_INSTALLED'


def test_ambiguity_negation_and_conflicts(enabled):
    text = 'not a car; a bike; 120kmph then 140kmph'
    facts = [mention('VEHICLE_CLASS', 'not a car', 'car'), mention('VEHICLE_CLASS', 'bike', certainty='ambiguous'),
             mention('OBSERVED_SPEED', '120kmph', '120'), mention('OBSERVED_SPEED', '140kmph', '140')]
    entities, meta = intake.interpret(text, provider=Provider(facts))
    assert not meta['fallbackUsed']
    assert entities[0]['status'] == 'unresolved' and entities[1]['status'] == 'ambiguous'
    assert [e['normalizedValue'] for e in entities[2:]] == ['120', '140']


def send(client, url, matter, value):
    response = client.post(url + '/answers', json={'revision': matter['revision'],
        'questionId': matter['currentQuestion']['id'], 'messageId': str(uuid4()), 'answer': value})
    assert response.status_code == 200, response.text
    return response.json()


def test_persist_before_question_and_keep_on_issue_confirmation(client, enabled, monkeypatch):
    provider = Provider(FACTS)
    monkeypatch.setattr(intake, 'OllamaProvider', lambda url: provider)
    m = client.post('/api/v1/matters', json={'originalText': EXAMPLE, 'language': 'english'}).json()
    url = '/api/v1/matters/' + m['id']
    m = client.post(url + '/analyze', json={'revision': m['revision']}).json()
    assert len(provider.calls) == 1 and m['nlpAnalysis']['extractionMetadata']['modelCalled']
    original = m['facts']
    assert len(original) == 4 and all(not f['confirmed'] for f in original)
    assert next(f for f in original if f['key'] == 'OBSERVED_SPEED')['approximate']
    if m['currentQuestion']['slot'] == 'INTENT':
        m = send(client, url, m, 'INT002')
    assert m['facts'] == original
    assert m['currentQuestion']['slot'] not in {'VEHICLE_CLASS', 'OBSERVED_SPEED'}
    assert client.get(url).json()['facts'] == original
    assert client.post(url + '/verify', json={'revision': m['revision']}).status_code == 409
    # Follow-up provides several extra facts as well as the requested one.
    provider.facts = [mention('STATE', 'Tamil Nadu'), mention('EVENT_DATE', '2026-10-21'), mention('ROAD_TYPE', 'highway')]
    m = send(client, url, m, 'Tamil Nadu; 2026-10-21; highway')
    assert provider.calls[-1][0] == 'llama3.2:3b-instruct-q4_K_M'
    assert {'STATE', 'EVENT_DATE', 'ROAD_TYPE'} <= {f['key'] for f in m['facts']}
    assert m['conversation']['extractionHistory'][-1]['method'] == 'local_slm'
    assert not m.get('currentQuestion') or m['currentQuestion']['slot'] not in {'VEHICLE_CLASS', 'OBSERVED_SPEED', 'STATE', 'EVENT_DATE'}


def test_initial_conflicts_survive_persistence(client, enabled, monkeypatch):
    provider = Provider([mention('OBSERVED_SPEED', '120kmph', '120'), mention('OBSERVED_SPEED', '140kmph', '140')])
    monkeypatch.setattr(intake, 'OllamaProvider', lambda url: provider)
    m = client.post('/api/v1/matters', json={'originalText': '120kmph then 140kmph', 'language': 'english'}).json()
    m = client.post('/api/v1/matters/' + m['id'] + '/analyze', json={'revision': m['revision']}).json()
    assert len(m['facts']) == 2 and m['conversation']['contradictions']
    assert not m['conversation']['contradictions'][0]['resolved']


def test_short_quote_cannot_remove_negation(enabled):
    entities, _ = intake.interpret('I was not in a car', provider=Provider([mention('VEHICLE_CLASS', 'car')]))
    assert entities[0]['status'] == 'unresolved'


@pytest.mark.parametrize('model_id', ['llama3.2-3b', 'mistral-7b'])
def test_ollama_adapter_receives_intake_schema(enabled, monkeypatch, model_id):
    monkeypatch.setenv('NYAYA_INTAKE_MODEL', model_id)
    requests = []
    def request(self, path, payload=None, timeout=2):
        requests.append((path, payload))
        if path == '/api/tags':
            return {'models': [{'name': intake.MODELS[model_id].runtime_name}]}
        return {'message': {'content': json.dumps({'facts': [mention('VEHICLE_CLASS', 'car')]})}}
    monkeypatch.setattr(intake.OllamaProvider, '_request', request)
    _, meta = intake.interpret('my car')
    assert not meta['fallbackUsed']
    path, payload = requests[-1]
    assert path == '/api/chat' and payload['model'] == intake.MODELS[model_id].runtime_name
    assert 'POLICE_INVOLVEMENT' in payload['format']['$defs']['Mention']['properties']['slot']['enum']
    assert payload['options']['temperature'] == 0


def test_followup_preserves_extras_when_target_missing(client, enabled, monkeypatch):
    provider = Provider(FACTS)
    monkeypatch.setattr(intake, 'OllamaProvider', lambda url: provider)
    m = client.post('/api/v1/matters', json={'originalText': EXAMPLE, 'language': 'english'}).json()
    url = '/api/v1/matters/' + m['id']
    m = client.post(url + '/analyze', json={'revision': m['revision']}).json()
    if m['currentQuestion']['slot'] == 'INTENT':
        m = send(client, url, m, 'INT002')
    target = m['currentQuestion']['slot']
    provider.facts = [mention('CITY', 'Chennai')]
    m = send(client, url, m, 'Chennai')
    assert any(f['key'] == 'CITY' for f in m['facts'])
    assert m['currentQuestion']['slot'] == target


class BusyGate:
    def acquire(self, **kwargs):
        return False
    def release(self):
        raise AssertionError('An unacquired gate must not be released')


def test_busy_falls_back_without_claiming_a_model_call(enabled, monkeypatch):
    monkeypatch.setattr(intake, '_gate', BusyGate())
    p = Provider()
    entities, meta = intake.interpret('my car at 150kmph', provider=p)
    assert meta['failureReason'] == 'INTAKE_BUSY'
    assert meta['fallbackUsed'] and meta['method'] == 'deterministic_fallback'
    assert not meta['modelCalled'] and not p.calls
    assert meta['entityCount'] == len(entities) and meta['fallbackLatencyMs'] >= 0
    assert any(e['type'] == 'OBSERVED_SPEED' and e['normalizedValue'] == '150' for e in entities)
    assert all(e['method'] != 'local_slm_extractive' for e in entities)


def test_busy_api_persists_facts_and_continues_questions(client, enabled, monkeypatch):
    monkeypatch.setattr(intake, '_gate', BusyGate())
    m = client.post('/api/v1/matters', json={'originalText': 'My car at 150kmph on highway', 'language': 'english'}).json()
    url = '/api/v1/matters/' + m['id']
    response = client.post(url + '/analyze', json={'revision': m['revision']})
    assert response.status_code == 200
    m = response.json()
    meta = m['nlpAnalysis']['extractionMetadata']
    assert meta['failureReason'] == 'INTAKE_BUSY' and meta['fallbackUsed']
    assert all('deterministic' not in w.lower() and 'slm' not in w.lower() for w in m['nlpAnalysis']['warnings'])
    assert all(not f['confirmed'] for f in m['facts'])
    assert any(f['key'] == 'OBSERVED_SPEED' for f in m['facts'])
    if m['currentQuestion'] and m['currentQuestion']['slot'] == 'INTENT':
        m = send(client, url, m, 'INT002')
    assert not m.get('currentQuestion') or m['currentQuestion']['slot'] not in {'OBSERVED_SPEED', 'VEHICLE_CLASS'}
    m = send(client, url, m, 'Tamil Nadu; 2026-10-21')
    assert m['conversation']['extractionHistory'][-1]['fallbackUsed']
    assert {'STATE','EVENT_DATE'} <= {f['key'] for f in m['facts']}
    assert client.get(url).json()['facts'] == m['facts']


def test_empty_fallback_still_has_honest_metadata(enabled, monkeypatch):
    monkeypatch.setattr(intake, '_gate', BusyGate())
    entities, meta = intake.interpret('hello')
    assert meta['fallbackUsed'] and meta['entityCount'] == len(entities)
    assert not meta['modelCalled']
