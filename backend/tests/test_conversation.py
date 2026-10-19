from uuid import uuid4

def _analyzed(client, text='I was driving my car at 120 km/h', language='auto', reference=None):
    created=client.post('/api/v1/matters',json={'originalText':text,'language':language}).json()
    url=f"/api/v1/matters/{created['id']}"
    response=client.post(url+'/analyze',json={'revision':created['revision'],'referenceDatetime':reference})
    assert response.status_code==200,response.text
    return url,response.json()

def test_question_answer_persistence_and_revision(client):
    url,matter=_analyzed(client)
    question=matter['currentQuestion']
    assert question and question['slot'] in matter['missingSlots']
    snapshot=client.get(url+'/questions/next').json()
    assert snapshot['question']==question
    assert client.get(url+'/questions/next').json()==snapshot
    payload={'revision':matter['revision'],'questionId':question['id'],'messageId':str(uuid4()),'answer':'I do not know'}
    answered=client.post(url+'/answers',json=payload)
    assert answered.status_code==200,answered.text
    updated=answered.json()
    assert question['slot'] in updated['conversation']['unknownSlots']
    assert question['slot'] in updated['missingSlots']
    assert updated['revision']==matter['revision']+1
    assert client.get(url).json()['messages']==updated['messages']
    assert client.post(url+'/answers',json=payload).status_code==409

def test_multifact_answer_and_verification_gate(client):
    url,matter=_analyzed(client,'I was driving at 120 km/h')
    question=matter['currentQuestion']
    answer=client.post(url+'/answers',json={'revision':matter['revision'],'questionId':question['id'],
        'messageId':str(uuid4()),'answer':'A car on an expressway in Tamil Nadu'})
    assert answer.status_code==200,answer.text
    updated=answer.json()
    keys={f['key'] for f in updated['facts']}
    assert {'VEHICLE_CLASS','ROAD_TYPE','STATE'}<=keys
    assert client.post(url+'/verify',json={'revision':updated['revision']}).status_code==409
    assert client.get(url+'/conversation').json()['revision']==updated['revision']

def test_fact_edit_confirmation_and_history(client):
    url,matter=_analyzed(client)
    fact=next(f for f in matter['facts'] if f['key']=='OBSERVED_SPEED')
    edited=client.patch(url+'/facts/'+fact['id'],json={'revision':matter['revision'],'value':'90 km/h'})
    assert edited.status_code==200,edited.text
    changed=edited.json()
    assert changed['conversation']['factHistory'][0]['previous']['value']==fact['value']
    assert next(f for f in changed['facts'] if f['id']==fact['id'])['confirmed'] is False
    confirmed=client.post(url+'/facts/'+fact['id']+'/confirm',json={'revision':changed['revision']})
    assert confirmed.status_code==200,confirmed.text
    item=next(f for f in confirmed.json()['facts'] if f['id']==fact['id'])
    assert item['provenance']=='USER_CONFIRMED'

def test_conflicting_claims_are_preserved_and_block_verification(client):
    url,matter=_analyzed(client,'My insurance expired')
    question=matter['currentQuestion']
    assert question
    answer=client.post(url+'/answers',json={'revision':matter['revision'],'questionId':question['id'],
        'messageId':str(uuid4()),'answer':'2026-10-19, and my insurance is active'})
    assert answer.status_code==200,answer.text
    updated=answer.json()
    conflicts=[c for c in updated['conversation']['contradictions'] if not c['resolved']]
    assert conflicts and conflicts[0]['slot']=='INSURANCE_STATUS'
    assert conflicts[0]['previous']['normalizedValue']=='expired'
    assert conflicts[0]['candidate']['normalizedValue']=='active'
    assert client.post(url+'/verify',json={'revision':updated['revision']}).status_code==409

def test_explicit_verification_and_protected_patch(client):
    url,matter=_analyzed(client,'I drove my car at 120 km/h on an expressway')
    assert matter['conversation']['reviewEligible']
    assert client.patch(url,json={'revision':matter['revision'],'stage':'USER_VERIFIED'}).status_code==409
    for fact in matter['facts']:
        result=client.post(url+'/facts/'+fact['id']+'/confirm',json={'revision':matter['revision']})
        assert result.status_code==200,result.text
        matter=result.json()
    verified=client.post(url+'/verify',json={'revision':matter['revision']})
    assert verified.status_code==200,verified.text
    assert verified.json()['stage']=='USER_VERIFIED'
    assert client.get(url).json()['verifiedAt']==verified.json()['verifiedAt']

def test_multilingual_templates_and_relative_date(client):
    _,hindi=_analyzed(client,'मेरी कार का चालान कटा।',language='hindi')
    assert hindi['currentQuestion']
    assert any('\u0900' <= character <= '\u097f' for character in hindi['currentQuestion']['question'])
    _,hinglish=_analyzed(client,'Mera challan kat gaya',language='hinglish')
    assert hinglish['currentQuestion']
    assert 'hai' in hinglish['currentQuestion']['question'].lower() or 'kab' in hinglish['currentQuestion']['question'].lower()
    _,dated=_analyzed(client,'My insurance expired yesterday',reference='2026-10-19T15:00:00+05:30')
    assert any(f['key']=='EVENT_DATE' and f['normalizedValue']=='2026-10-18' for f in dated['facts'])

def test_unknowns_require_acknowledgement_without_faking_completeness(client):
    url,matter=_analyzed(client,'I drove at 120 km/h')
    for _ in range(5):
        question=matter.get('currentQuestion')
        if not question:break
        response=client.post(url+'/answers',json={'revision':matter['revision'],'questionId':question['id'],
            'messageId':str(uuid4()),'answer':"I don't know"})
        assert response.status_code==200,response.text
        matter=response.json()
    assert matter['conversation']['reviewEligible']
    assert matter['missingSlots']
    assert matter['contextReadiness']['found']<matter['contextReadiness']['total']
    for fact in matter['facts']:
        if fact.get('resolutionStatus')=='resolved':
            response=client.post(url+'/facts/'+fact['id']+'/confirm',json={'revision':matter['revision']})
            assert response.status_code==200,response.text
            matter=response.json()
    assert client.post(url+'/verify',json={'revision':matter['revision']}).status_code==409
    verified=client.post(url+'/verify',json={'revision':matter['revision'],'acknowledgeUnknowns':True})
    assert verified.status_code==200,verified.text
    assert verified.json()['conversation']['unknownsAcknowledged']

def test_urgent_accident_notice_precedes_ordinary_question(client):
    _,matter=_analyzed(client,'My car hit another vehicle and someone is injured')
    messages=matter['messages']
    urgent=next(i for i,item in enumerate(messages) if item['id']=='urgent-assistance')
    question=next(i for i,item in enumerate(messages) if item['id'].startswith('q-'))
    assert urgent<question
    assert '112' in messages[urgent]['text']
