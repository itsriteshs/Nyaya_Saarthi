from uuid import uuid4

def analyzed(client,text):
    m=client.post('/api/v1/matters',json={'originalText':text,'language':'english'}).json()
    url='/api/v1/matters/'+m['id']
    return url,client.post(url+'/analyze',json={'revision':m['revision']}).json()

def answer(client,url,m,value):
    response=client.post(url+'/answers',json={'revision':m['revision'],'questionId':m['currentQuestion']['id'],
        'messageId':str(uuid4()),'answer':value})
    assert response.status_code==200,response.text
    return response.json()

def test_uncertain_prediction_does_not_choose_workflow_without_user(client):
    url,m=analyzed(client,'I drove at 95 km/h')
    assert m['nlpAnalysis']['intent']['needsClarification']
    assert m['currentQuestion']['slot']=='INTENT'
    assert client.post(url+'/verify',json={'revision':m['revision'],'acknowledgeUnknowns':True}).status_code==409
    original=m['nlpAnalysis']['intent'].copy()
    m=answer(client,url,m,'INT032')
    assert m['nlpAnalysis']['intent']['id']=='INT032'
    assert m['conversation']['originalIntentPrediction']==original
    assert m['conversation']['selectedIntentId']=='INT032'
    assert m['nlpAnalysis']['intent']['scoreType'].startswith('User-selected')
    assert m['currentQuestion']['slot']!='INTENT'

def test_outside_scope_cannot_verify_even_with_unknown_acknowledgement(client):
    url,m=analyzed(client,'What is a good recipe for bread?')
    m=answer(client,url,m,'OUT_OF_SCOPE')
    assert m['conversation']['intentUnsupported']
    assert not m.get('currentQuestion')
    assert not m['conversation']['reviewEligible']
    assert client.post(url+'/verify',json={'revision':m['revision'],'acknowledgeUnknowns':True}).status_code==409
    assert not m.get('guidance')

def test_another_domain_exposes_all_ontology_choices(client):
    url,m=analyzed(client,'I need help with a vehicle question')
    m=answer(client,url,m,'OTHER')
    assert m['currentQuestion']['slot']=='INTENT_DOMAIN'
    domain=m['currentQuestion']['options'][0]['value']
    m=answer(client,url,m,domain)
    assert m['currentQuestion']['slot']=='INTENT_DETAIL'
    choice=next(o['value'] for o in m['currentQuestion']['options'] if o['value'].startswith('INT'))
    m=answer(client,url,m,choice)
    assert m['conversation']['selectedIntentId']==choice


def test_scoped_status_witness_and_hindi_state_variants():
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    cases=[('My permit expired.', 'PERMIT_STATUS','expired'),
           ('My pollution certificate expired.', 'PUC_STATUS','expired'),
           ('मेरा लाइसेंस एक्सपायर हो गया।', 'LICENCE_STATUS','expired'),
           ('यह केरल में हुआ।', 'STATE','Kerala'),
           ('यह कर्नाटक में हुआ।', 'STATE','Karnataka'),
           ('I witnessed a collision.', 'USER_ROLE','witness'),
           ('Nobody was injured.', 'INJURY_PRESENT','no')]
    for text,kind,value in cases:
        entities=[normalize(e) for e in extract(text,status_values={})]
        assert any(e['type']==kind and e['normalizedValue']==value for e in entities),(text,entities)
    for text in ['My licence is not expired.', 'My insurance claim is over.']:
        entities=[normalize(e) for e in extract(text,status_values={})]
        assert not any(e['type'] in {'LICENCE_STATUS','INSURANCE_STATUS'} and e['normalizedValue']=='expired' and e['status']=='resolved' for e in entities)


def test_canonical_vehicle_codes_are_accepted_without_guessing_weights():
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    for text,expected in [('HGV','VC_HGV'),('Medium Goods Vehicle','VC_MGV'),('VC_MOTORCAR','VC_MOTORCAR')]:
        entities=[normalize(e) for e in extract(text,status_values={})]
        assert any(e['type']=='VEHICLE_CLASS' and e['normalizedId']==expected for e in entities)
    entities=[normalize(e) for e in extract('truck',status_values={})]
    assert entities[0]['status']=='ambiguous'


def test_negated_vehicle_does_not_replace_the_corrected_vehicle():
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    for text in ['I meant a car, not a bike.', 'Not a motorcycle; a car.']:
        vehicles=[normalize(e) for e in extract(text,status_values={}) if e['type']=='VEHICLE_CLASS']
        assert len(vehicles)==1 and vehicles[0]['normalizedId']=='VC_MOTORCAR'


def test_schema_date_destination_and_vehicle_answers_normalize():
    from app.services.conversation import _target_entity
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    for slot,text,expected in [('LICENCE_EXPIRY_DATE','2026-09-14','2026-09-14'),
                               ('DESTINATION_STATE','Punjab','Punjab'),
                               ('VEHICLE_CLASS','HEAVY_GOODS_VEHICLE','Heavy Goods Vehicle')]:
        entity=_target_entity(slot,text,[normalize(e) for e in extract(text,status_values={})])
        assert entity and entity['status']=='resolved'
        assert entity['normalizedValue']==expected
        if slot=='VEHICLE_CLASS':assert entity['normalizedId']=='VC_HGV'


def test_startup_warms_local_index_before_serving(monkeypatch,tmp_path):
    import asyncio
    from app import main
    (tmp_path/'manifest.json').write_text('{}')
    calls=[]
    monkeypatch.setenv('NYAYA_WARM_LEGAL_INDEX','true')
    monkeypatch.setattr(main,'INDEX_DIR',tmp_path)
    monkeypatch.setattr(main,'load_index',lambda: calls.append('loaded'))
    async def check():
        async with main.lifespan(main.app):
            assert calls==['loaded']
    asyncio.run(check())


def test_missing_date_and_state_prevent_operational_review(client):
    from workflow_helpers import establish_issue
    url,m=analyzed(client,'I drive a car at 65 km/h on a city road')
    m=establish_issue(client,url,m,'INT002')
    assert {'STATE','EVENT_DATE'}<=set(m['missingSlots'])
    assert not m['conversation']['reviewEligible']
    assert client.post(url+'/verify',json={'revision':m['revision'],'acknowledgeUnknowns':True}).status_code==409


def test_optional_ambiguous_mentions_cannot_deadlock_verify(client):
    from workflow_helpers import establish_issue
    url,m=analyzed(client,'My car hit a scooter on 2026-10-19 in Kerala. Injury status: yes')
    m=establish_issue(client,url,m,'INT053')
    assert m['currentQuestion']['slot']=='VEHICLE_CLASS'
    assert 'More than one vehicle' in m['currentQuestion']['question']
    assert not m['conversation']['reviewEligible']
    m=answer(client,url,m,'car')
    vehicles=[f for f in m['facts'] if f['key']=='VEHICLE_CLASS']
    assert len(vehicles)==1 and vehicles[0]['normalizedId']=='VC_MOTORCAR'
    assert m['conversation']['reviewEligible']


def test_explicit_injuries_are_not_asked_again_and_hypotheticals_are_not_asserted():
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    for text in ['The passenger is bleeding.', 'Someone was badly injured.']:
        entities=[normalize(e) for e in extract(text,status_values={})]
        assert any(e['type']=='INJURY_PRESENT' and e['normalizedValue']=='yes' for e in entities)
    for text in ['If someone is injured, what happens?', 'Nobody was injured.']:
        entities=[normalize(e) for e in extract(text,status_values={})]
        assert not any(e['type']=='INJURY_PRESENT' and e['normalizedValue']=='yes' for e in entities)


def test_licence_entitlement_is_not_an_incident_vehicle_fact():
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    for label in ['licence class','license class','लाइसेंस वर्ग']:
        entities=[normalize(e) for e in extract(f'A scooter. {label}: LMV.',status_values={})]
        vehicles=[e for e in entities if e['type']=='VEHICLE_CLASS']
        assert len(vehicles)==1 and vehicles[0]['text']=='scooter'
        assert any(e['type']=='LICENCE_CLASS' and e['normalizedValue']=='LMV' for e in entities)
