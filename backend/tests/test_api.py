from uuid import uuid4

def test_health_and_docs(client):
    assert client.get('/api/v1/health').json() == {'status':'ok','service':'nyayasaarthi-backend','version':'0.1.0'}
    assert client.get('/docs').status_code == 200

def test_dataset_endpoints(client):
    summary = client.get('/api/v1/datasets/summary')
    assert summary.status_code == 200
    assert summary.json()['dataset_count'] == 23
    assert client.get('/api/v1/datasets/validation').json()['status'] == 'completed'

def test_matter_lifecycle(client):
    base = '/api/v1/matters'
    created = client.post(base, json={'originalText':' A road situation ','language':'hinglish'})
    assert created.status_code == 201
    matter = created.json()
    assert matter['originalText'] == 'A road situation'
    assert matter['stage'] == 'DRAFT' and matter['revision'] == 1
    url = f"{base}/{matter['id']}"
    assert client.get(url).json()['id'] == matter['id']
    changed = client.patch(url, json={'revision':1,'stage':'UNDERSTANDING','answers':{'vehicle_type':'car'}})
    assert changed.status_code == 200
    assert changed.json()['revision'] == 2
    assert changed.json()['answers']['vehicle_type'] == 'car'
    assert client.get(url).json()["stage"] == "UNDERSTANDING"
    assert client.patch(url, json={'revision':1,'stage':'COMPLETED'}).status_code == 409
    assert client.patch(url, json={'revision':2,'id':str(uuid4())}).status_code == 422
    assert client.patch(url, json={'revision':2,'stage':'INVALID'}).status_code == 422
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404

def test_invalid_requests(client):
    base='/api/v1/matters'
    assert client.post(base, json={'originalText':'x','language':'invalid'}).status_code == 422
    assert client.post(base, json={'originalText':' ','language':'auto'}).status_code == 422
    assert client.get(f'{base}/{uuid4()}').status_code == 404
    assert client.get(f'{base}/bad-id').status_code == 422

def test_cors_and_size_limit(client):
    allowed = client.options('/api/v1/matters', headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'POST'})
    assert allowed.headers.get('access-control-allow-origin') == 'http://localhost:3000'
    denied = client.options('/api/v1/matters', headers={'Origin':'https://example.com','Access-Control-Request-Method':'POST'})
    assert 'access-control-allow-origin' not in denied.headers
    assert client.post('/api/v1/matters', content=b'x' * 256001).status_code == 413

def test_realistic_context_round_trip(client):
    """Exercise the current UI's clarification, verification, and guidance shape."""
    created = client.post('/api/v1/matters', json={
        'originalText': 'I was driving at 90 km/h on an expressway.', 'language': 'english'
    })
    assert created.status_code == 201
    matter = created.json()
    assert 'verifiedAt' not in matter and 'currentQuestion' not in matter
    url = f"/api/v1/matters/{matter['id']}"
    first = client.patch(url, json={
        'revision': matter['revision'],
        'intent': {'label': 'Possible speeding / traffic violation', 'descriptor': 'Speed context'},
        'facts': [{'id': 'speed', 'key': 'speed', 'label': 'Speed', 'value': '90 km/h',
                   'state': 'provided', 'provenance': 'USER_PROVIDED', 'confirmed': False}],
        'missingSlots': ['vehicle_type'],
        'contextReadiness': {'found': 1, 'total': 2},
        'stage': 'UNDERSTANDING',
        'currentQuestion': {'slot': 'vehicle_type', 'question': 'What vehicle?', 'type': 'options',
                            'options': [{'label': 'Car', 'value': 'car'}], 'why': 'Vehicle class matters'},
        'messages': [{'id': 'user-initial', 'speaker': 'user', 'text': 'I was driving at 90 km/h on an expressway.'},
                     {'id': 'assistant-intro', 'speaker': 'assistant', 'text': 'What vehicle?'}],
    })
    assert first.status_code == 200
    assert first.json()['currentQuestion']['slot'] == 'vehicle_type'
    assert 'requiresConfirmation' not in first.json()['facts'][0]
    second = client.patch(url, json={
        'revision': first.json()['revision'], 'answers': {'vehicle_type': 'car'},
        'missingSlots': [], 'currentQuestion': None, 'stage': 'USER_VERIFIED',
        'verifiedAt': '2026-10-19T10:00:00Z',
        'facts': [{**first.json()['facts'][0], 'state': 'confirmed',
                   'provenance': 'USER_CONFIRMED', 'confirmed': True}],
    })
    assert second.status_code == 200
    retrieved = client.get(url).json()
    assert retrieved['answers']['vehicle_type'] == 'car'
    assert retrieved['verifiedAt'].startswith('2026-10-19T10:00:00')
    assert 'currentQuestion' not in retrieved
    guidance = {'generatedAt': '2026-10-19T10:01:00Z', 'directAnswer': 'Prototype guidance',
                'qualification': 'Unverified prototype', 'sources': [], 'mappings': [],
                'uncertainties': ['Needs source review'], 'nextSteps': [], 'suggestedQuestions': []}
    third = client.patch(url, json={'revision': retrieved['revision'], 'stage': 'GUIDANCE_GENERATED',
                                    'guidance': guidance})
    assert third.status_code == 200
    assert client.get(url).json()['guidance'] == guidance
    assert client.patch(url, json={'revision': third.json()['revision'], 'stage': None}).status_code == 422

def test_nested_matter_contract_validation(client):
    created = client.post('/api/v1/matters', json={'originalText': 'Vehicle situation', 'language': 'auto'}).json()
    url = f"/api/v1/matters/{created['id']}"
    assert client.patch(url, json={'revision': 1, 'contextReadiness': {'found': 2, 'total': 1}}).status_code == 422
    assert client.patch(url, json={'revision': 1, 'currentQuestion': {
        'slot': 'vehicle_type', 'question': 'Which vehicle?', 'type': 'options',
        'options': [{'foo': 'bar'}], 'why': 'Context'
    }}).status_code == 422
    assert client.get(url).json()['revision'] == 1
