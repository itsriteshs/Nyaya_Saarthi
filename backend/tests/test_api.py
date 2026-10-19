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
