"""Dataset-driven planner with validated SLM-first fact answers on the existing matter record."""
from datetime import datetime, timezone
import json
import re
from uuid import uuid4
from app.services.nlp.ontology import ontology
from app.services.nlp.entity_extractor import extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.slm_extractor import interpret
from app.services.nlp.language import analyze_language
from app.services.nlp.slot_detector import detect_slots

UNKNOWN = re.compile(r"^(?:i\s+(?:do\s+not|don't)\s+know|not\s+sure|i\s+can't\s+remember|skip|mujhe\s+nahi\s+pata|pata\s+nahi|पता\s+नहीं)[.!\s]*$", re.I)
TIMELINE = re.compile(r"\b(?:yesterday|today|last\s+month|renewed|before|after|previously|now)\b|कल|आज|पहले|अब", re.I)
POSITIVE = re.compile(r"^(?:yes|haan|ha|हाँ|जी\s+हाँ)$", re.I)
NEGATIVE = re.compile(r"^(?:no|nahi|नहीं)$", re.I)
BOOL_SLOTS = {'INJURY_PRESENT','DEATH_PRESENT','OTHER_VEHICLE_IDENTIFIED','EVIDENCE_AVAILABLE','POLICE_REPORTED'}
TEXT_SLOTS = {'CITY','LOCATION','ROAD_NAME','USER_ROLE','LICENCE_CLASS','REGISTRATION_NUMBER'}
DATE_SLOTS = {'EVENT_DATE','CHALLAN_DATE'}

def now(): return datetime.now(timezone.utc).isoformat()

def state(context):
    return context.setdefault('conversation', {'askedSlots':[], 'unknownSlots':[], 'contradictions':[],
        'factHistory':[], 'displayLanguage':'english', 'reviewEligible':False,
        'unresolvedRequirements':[], 'ambiguousSlots':[], 'urgentAssistance':False})

def _language(context):
    if context['language'] != 'auto': return context['language']
    detected = context.get('nlpAnalysis',{}).get('language',{}).get('detectedLanguage')
    return detected if detected in {'english','hindi','hinglish'} else 'english'

def _rows(context):
    intent=context.get('nlpAnalysis',{}).get('intent',{}).get('id')
    rows=list(ontology()['slots'].get(intent,[]))
    # Admissible retrieval always needs a jurisdiction and applicability date.
    # This operational gate is separate from evaluation-label schema requirements.
    present={r['slot_name'] for r in rows}
    for row in ontology()['slots'].get('INT001',[]):
        if row['slot_name'] in {'STATE','EVENT_DATE'} and row['slot_name'] not in present:
            rows.append(dict(row))
    return sorted(rows,key=lambda r:(int(r['ask_priority'] or 999),r['slot_id']))

def _label(context, slot):
    return next((r['slot_display_name'] for r in _rows(context) if r['slot_name']==slot),slot.replace('_',' ').title())

def _question(context, slot, reason='missing'):
    row=next((r for r in _rows(context) if r['slot_name']==slot),None)
    if row is None:row=next((r for group in ontology()['slots'].values() for r in group if r['slot_name']==slot),None)
    lang=state(context)['displayLanguage']
    column={'hindi':'question_template_hi','hinglish':'question_template_hinglish'}.get(lang,'question_template_en')
    template=(row or {}).get(column) or (row or {}).get('question_template_en') or f'Please clarify {_label(context,slot)}.'
    if slot=='VEHICLE_CLASS' and any(
        f['key']==slot and f.get('resolutionStatus')=='ambiguous'
        and re.search(r'motorcycle|bike|scooter|मोटरसाइकिल|स्कूटर',f.get('value',''),re.I)
        for f in context.get('facts',[])
    ):
        template={
            'hindi':'आपकी मोटरसाइकिल या स्कूटर गियर वाला है या बिना गियर का? MCWG या MCWOG भी लिख सकते हैं।',
            'hinglish':'Aapki motorcycle ya scooter geared hai ya gearless? MCWG ya MCWOG bhi likh sakte hain.',
        }.get(lang,'Is your motorcycle or scooter geared or gearless? You can answer MCWG or MCWOG.')
    if slot=='VEHICLE_CLASS' and len({f.get('value','').casefold() for f in context.get('facts',[]) if f['key']==slot})>1:
        template={'hindi':'एक से अधिक वाहन बताए गए हैं। आपका प्रश्न किस वाहन के बारे में है?',
                  'hinglish':'Ek se zyada vehicles bataye gaye hain. Aapka sawal kis vehicle ke baare mein hai?'}.get(lang,
                  'More than one vehicle was mentioned. Which vehicle is your question about?')
    if slot=='OBSERVED_SPEED' and any(f['key']==slot and f.get('unit')=='unknown' for f in context.get('facts',[])):
        template='What unit was your reported speed in? For example, km/h. The numeric value is already recorded.'
    unresolved_fact=next((f for f in context.get('facts',[]) if f['key']==slot and
                          f.get('resolutionStatus') in {'ambiguous','unresolved'}),None)
    if slot in {'STATE','DESTINATION_STATE'} and unresolved_fact:
        value=unresolved_fact.get('value','that answer')
        template={
            'hindi':f'मैं “{value}” को राज्य या केंद्र शासित प्रदेश के रूप में पुष्टि नहीं कर पाया। कृपया उसका पूरा नाम लिखें।',
            'hinglish':f'Main “{value}” ko State ya Union Territory ke roop mein confirm nahi kar paya. Kripya uska poora naam likhein.',
        }.get(lang,f'I could not confirm “{value}” as a State or Union Territory. Please enter its full name.')
    if slot=='VEHICLE_CLASS' and unresolved_fact and not any(
        f['key']==slot and f.get('resolutionStatus')=='ambiguous'
        and re.search(r'motorcycle|bike|scooter|मोटरसाइकिल|स्कूटर',f.get('value',''),re.I)
        for f in context.get('facts',[])
    ):
        value=unresolved_fact.get('value','that answer')
        template={
            'hindi':f'मैं “{value}” को वाहन के प्रकार के रूप में पहचान नहीं पाया। कृपया कार, मोटरसाइकिल या स्कूटर जैसा वाहन बताएं।',
            'hinglish':f'Main “{value}” ko vehicle type ke roop mein pehchan nahi paya. Kripya car, motorcycle ya scooter jaisa vehicle batayein.',
        }.get(lang,f'I could not identify “{value}” as a vehicle type. Please name the vehicle (for example, car, motorcycle, or scooter).')
    if reason=='contradiction':
        template=f"Two answers about {_label(context,slot)} differ. Which describes the event? {template}"
    return {'id':f"q-{slot}-{len(state(context)['askedSlots'])+1}", 'slot':slot,'question':template,
            'type':'text','why':(row or {}).get('why_legally_relevant') or 'This detail helps establish the context.'}

def _has_value(fact):
    return fact.get('state') != 'unknown' and fact.get('resolutionStatus','resolved') == 'resolved' and bool(fact.get('normalizedValue') or fact.get('value'))

def _intent_question(context):
    conv=state(context)
    language=conv['displayLanguage']
    stage=conv.get('intentQuestionStage','candidate')
    intents=ontology()['intents']
    if stage=='domain':
        options=[{'label':domain,'value':'DOMAIN:'+domain} for domain in sorted({r['domain'] for r in intents.values()})]
        prompt='Which motor-vehicle law area best describes your question?'
        slot='INTENT_DOMAIN'
    elif stage=='detail':
        options=[{'label':r['intent_name'].replace('_',' ').title(),'value':r['intent_id']}
                 for r in intents.values() if r['domain']==conv.get('intentDomain')]
        prompt='Which issue would you like help with first?'
        slot='INTENT_DETAIL'
    else:
        prediction=context['nlpAnalysis']['intent']
        ids=[prediction['id']]+[a['id'] for a in prediction.get('alternatives',[])]
        options=[{'label':intents[i]['intent_name'].replace('_',' ').title(),'value':i} for i in dict.fromkeys(ids) if i in intents]
        prompt={'hindi':'मुद्दा स्पष्ट नहीं है। पहले किस विषय में मदद चाहिए?',
                'hinglish':'Issue clear nahi hai. Pehle kis mudde par madad chahiye?'}.get(language,
                'The issue is uncertain. Which issue would you like help with first?')
        slot='INTENT'
    options += [{'label':'Another motor-vehicle issue','value':'OTHER'},
                {'label':'Outside motor-vehicle law / none of these','value':'OUT_OF_SCOPE'}]
    return {'id':'q-intent-'+str(len(conv['askedSlots'])+1),'slot':slot,'type':'options',
            'question':prompt,'options':options,
            'why':'Confirm the topic before asking issue-specific questions. A model prediction is not a confirmed fact.'}


def _resolve_intent(context,answer):
    conv=state(context);clean=answer.strip();intents=ontology()['intents']
    if clean=='OTHER':conv['intentQuestionStage']='domain'
    elif clean.startswith('DOMAIN:') and clean[7:] in {r['domain'] for r in intents.values()}:
        conv['intentDomain']=clean[7:];conv['intentQuestionStage']='detail'
    elif clean=='OUT_OF_SCOPE' or UNKNOWN.fullmatch(clean):
        conv['intentUnsupported']=True
        context['messages'].append({'id':str(uuid4()),'speaker':'assistant','text':
            'The issue has not been established as a supported motor-vehicle-law question. No legal guidance will be generated. You can start a new situation with a supported question.'})
    else:
        selected=next((r for r in intents.values() if clean.casefold() in {
            r['intent_id'].casefold(),r['intent_name'].casefold(),r['intent_name'].replace('_',' ').casefold()}),None)
        if not selected:
            context['messages'].append({'id':str(uuid4()),'speaker':'assistant','text':'Please select a listed issue, another motor-vehicle issue, or outside scope.'})
            return
        previous=dict(context['nlpAnalysis']['intent'])
        conv.setdefault('originalIntentPrediction',previous)
        conv['intentConfirmed']=True;conv['selectedIntentId']=selected['intent_id']
        context['nlpAnalysis']['intent'].update(id=selected['intent_id'],name=selected['intent_name'],domain=selected['domain'],
            score=0,scoreType='User-selected workflow, not a model prediction',marginGap=0,needsClarification=False,alternatives=[])
        context['intent']={'label':selected['intent_name'].replace('_',' ').title(),'descriptor':selected['domain']+' · Selected by you'}
        original_slots={k:context['nlpAnalysis'].get(k) for k in ('missingSlots','unresolvedSlots','readiness')}
        conv.setdefault('originalSlotAnalysis',original_slots)
        context['nlpAnalysis'].update(detect_slots(selected['intent_id'],context['nlpAnalysis']['entities']))
        conv['factHistory'].append({'action':'select_intent','previous':previous,'selectedIntentId':selected['intent_id'],'at':now()})
        context['nlpAnalysis']['warnings']=[w for w in context['nlpAnalysis'].get('warnings',[]) if not w.startswith('Intent classifier is uncertain')]
        context['nlpAnalysis']['warnings'].append('Workflow explicitly selected by the user; this is not an improved classifier prediction.')
        context.pop('guidance',None);context.pop('verifiedAt',None)


def recompute(context):
    """Only required/intent-context schema rows block completeness; unsupported conditions stay visible."""
    conv=state(context)
    if context.get('nlpAnalysis',{}).get('intent',{}).get('needsClarification') and not conv.get('intentConfirmed'):
        conv['reviewEligible']=False;conv['verificationEligible']=False
        context['stage']='NEEDS_CLARIFICATION'
        context['missingSlots']=['INTENT']
        context['contextReadiness']={'found':0,'total':1}
        context['intent']={'label':'Outside supported scope' if conv.get('intentUnsupported') else 'Issue needs confirmation',
                           'descriptor':'No legal guidance will be generated.' if conv.get('intentUnsupported') else 'The model prediction has not been confirmed.'}
        if conv.get('intentUnsupported'):
            context['currentQuestion']=None
        else:
            active=context.get('currentQuestion')
            if not active or active['slot'] not in {'INTENT','INTENT_DOMAIN','INTENT_DETAIL'}:
                context['currentQuestion']=_intent_question(context)
                conv['askedSlots'].append(context['currentQuestion']['slot'])
                context['messages'].append({'id':context['currentQuestion']['id'],'speaker':'assistant','text':context['currentQuestion']['question']})
        return context
    facts={f['key']:f for f in context.get('facts',[]) if _has_value(f)}
    conflicted={c['slot'] for c in conv['contradictions'] if not c.get('resolved')}
    ambiguous={f['key'] for f in context.get('facts',[]) if f.get('resolutionStatus') in {'ambiguous','unresolved'}}
    conv['ambiguousSlots']=sorted(ambiguous)
    entities=[{'type':f['key'],'normalizedValue':f.get('normalizedValue') or f['value'],
               'status':'unresolved' if f['key'] in conflicted else f.get('resolutionStatus','resolved')}
              for f in context.get('facts',[]) if f.get('state')!='unknown']
    detected=detect_slots(context.get('nlpAnalysis',{}).get('intent',{}).get('id'),entities,
                          required_slots={'STATE','EVENT_DATE'}, configured_rows=_rows(context))
    missing=[item['slot'] for item in detected['missingSlots']]
    unresolved=detected['unresolvedSlots']
    found=detected['readiness']['found'];total=detected['readiness']['total']
    conv['unresolvedRequirements']=unresolved
    context['nlpAnalysis']['unresolvedSlots']=unresolved
    context['missingSlots']=missing
    context['contextReadiness']={'found':found,'total':total}
    candidates=[s for s in set(missing)|ambiguous if s not in conv['unknownSlots']]
    candidates=sorted(set(candidates)|conflicted,key=lambda s:next((i for i,r in enumerate(_rows(context)) if r['slot_name']==s),999))
    active=context.get('currentQuestion')
    if active and active['slot'] in candidates:
        next_question=active
    elif candidates:
        slot=candidates[0]
        next_question=_question(context,slot,'contradiction' if slot in conflicted else 'missing')
        conv['askedSlots'].append(slot)
        context['messages'].append({'id':next_question['id'],'speaker':'assistant','text':next_question['question']})
    else:next_question=None
    context['currentQuestion']=next_question
    conv['reviewEligible']=not candidates and not conflicted
    conv['confirmationPending']=[f['id'] for f in context.get('facts',[]) if _has_value(f) and not f.get('confirmed')]
    conv['verificationEligible']=conv['reviewEligible'] and not conv['confirmationPending'] and not conv['unknownSlots']
    context['stage']='READY_FOR_REVIEW' if conv['reviewEligible'] else 'NEEDS_CLARIFICATION'
    return context

def needs_urgent_assistance(text):
    # Evaluate each injury mention independently: negating one must not hide another.
    for match in re.finditer(r'\b(?:injur(?:y|ies|ed)|bleeding|unconscious)\b|घायल|खून बह|बेहोश|serious accident|गंभीर दुर्घटना',text,re.I):
        prefix=re.split(r'[.!?;।,]|\bbut\b',text[:match.start()],flags=re.I)[-1]
        if re.search(r'\b(?:no|not|nobody|none|without)\b[^.!?;।,]{0,35}$',prefix,re.I):
            continue
        suffix=text[match.end():match.end()+20]
        if re.match(r'\s*(?:नहीं|नही)',suffix):continue
        return True
    return False


def initialize(context):
    conv=state(context);conv['displayLanguage']=_language(context)
    conv['urgentAssistance']=needs_urgent_assistance(context['originalText'])
    for index,fact in enumerate(context['facts']):
        entity=context['nlpAnalysis']['entities'][index]
        fact.update(normalizedValue=entity.get('normalizedValue'),normalizedId=entity.get('normalizedId'),
                    sourceMessageId='user-initial',extractionMethod=entity.get('method'),
                    resolutionStatus=entity['status'],sourceText=entity['text'],
                    unit=entity.get('unit'),approximate=entity.get('approximate'),uncertainty=entity.get('uncertainty'),updatedAt=now())
    first_by_slot={}
    for fact in context['facts']:
        if not _has_value(fact) and not (fact['key']=='OBSERVED_SPEED' and fact.get('normalizedValue')):continue
        prior=first_by_slot.get(fact['key'])
        if prior and str(prior.get('normalizedValue') or prior['value'])!=str(fact.get('normalizedValue') or fact['value']):
            conv['contradictions'].append({'id':str(uuid4()),'slot':fact['key'],'previous':prior.copy(),
                'candidate':fact.copy(),'kind':'possible_timeline' if TIMELINE.search(context['originalText']) else 'different_values',
                'resolved':False,'createdAt':now()})
        else:first_by_slot[fact['key']]=fact
    if conv['urgentAssistance']:
        context['messages'].append({'id':'urgent-assistance','speaker':'assistant',
            'text':'If someone is injured or in immediate danger, seek urgent medical help and contact local emergency services. In India, 112 is the emergency response number. Legal questions can wait until people are safe.'})
    return recompute(context)

def _target_entity(slot, answer, entities, reference_datetime=None):
    clean=answer.strip()
    # A clear answer to a slot-specific question is authoritative user input.
    # Do not let an SLM certainty label override an exact ontology/schema value.
    if slot in {'STATE','DESTINATION_STATE'}:
        state=normalize({'type':'STATE','text':clean,'value':clean,'method':'question_context'})
        if state.get('status')=='resolved':
            state['type']=slot
            return state
    if slot=='VEHICLE_CLASS':
        subtype={'geared':'MCWG','with gear':'MCWG','with gears':'MCWG',
                 'gearless':'MCWOG','without gear':'MCWOG','without gears':'MCWOG'}
        value=subtype.get(clean.casefold())
        vehicle=normalize({'type':slot,'text':value or clean,'value':value or clean,'method':'question_context'})
        if vehicle.get('status')=='resolved' or (vehicle.get('status')=='ambiguous' and vehicle.get('alternatives')):
            return vehicle
    row=next((r for group in ontology()['slots'].values() for r in group if r['slot_name']==slot),None)
    if row and row.get('data_type')=='categorical':
        allowed={value.casefold().replace('_',' '):value.casefold() for value in row.get('allowed_values','').split('|')}
        matched=allowed.get(clean.casefold().replace('_',' '))
        if matched and matched!='unknown':
            return {'type':slot,'text':clean,'value':clean,'normalizedValue':matched,'normalizedId':None,
                    'status':'resolved','method':'question_context_allowed_value','alternatives':[]}
        if slot=='ROAD_TYPE' and len(clean)>1:
            return {'type':slot,'text':clean,'value':clean,'normalizedValue':'other','normalizedId':None,
                    'status':'resolved','method':'question_context_other','vocabularySource':'unclassified road context','alternatives':[]}
    if slot.endswith('_DATE') or (row and row.get('data_type')=='date'):
        dated=[normalize(e) for e in extract(clean,reference_datetime) if e['type'] in {'EVENT_DATE','CHALLAN_DATE'}]
        resolved=next((e for e in dated if e.get('status')=='resolved'),None)
        if resolved:
            resolved['type']=slot
            return resolved
    matches=[e for e in entities if e['type']==slot]
    if slot.endswith('_DATE') and not matches: matches=[e for e in entities if e['type']=='EVENT_DATE']
    if slot=='DESTINATION_STATE' and not matches: matches=[e for e in entities if e['type']=='STATE']
    # Prefer a resolved SLM candidate; if it is uncertain, fall through to the
    # slot-specific conservative normalization below rather than looping.
    resolved=next((e for e in matches if e.get('status')=='resolved'),None)
    if resolved:return resolved
    if slot=='VEHICLE_CLASS':
        subtype={'geared':'MCWG','with gear':'MCWG','with gears':'MCWG',
                 'gearless':'MCWOG','without gear':'MCWOG','without gears':'MCWOG'}
        value=subtype.get(clean.casefold())
        if value:
            return normalize({'type':slot,'text':value,'value':value,'method':'question_context'})
    if slot=='VEHICLE_CLASS':
        entity=normalize({'type':slot,'text':clean.replace('_',' '),'value':clean,'method':'question_context'})
        if entity['status'] in {'resolved','ambiguous'}:return entity
        return None
    if matches:return matches[0]
    if slot=='OBSERVED_SPEED':
        match=re.fullmatch(r'(?:about|around|maybe|लगभग)?\s*(\d{1,3})(?:\s*(?:km/h|kmph|kph))?',clean,re.I)
        if match:return {'type':slot,'text':clean,'value':match.group(1),'normalizedValue':match.group(1),
                         'normalizedId':None,'status':'resolved','method':'question_context','alternatives':[]}
    if slot in BOOL_SLOTS and (POSITIVE.fullmatch(clean) or NEGATIVE.fullmatch(clean)):
        return {'type':slot,'text':clean,'value':clean,'normalizedValue':'yes' if POSITIVE.fullmatch(clean) else 'no',
                'normalizedId':None,'status':'resolved','method':'question_context','alternatives':[]}
    if slot in DATE_SLOTS or (row and row.get('data_type')=='date'):
        from datetime import date
        try:
            value=date.fromisoformat(clean).isoformat()
            return {'type':slot,'text':clean,'value':clean,'normalizedValue':value,'normalizedId':None,
                    'status':'resolved','method':'question_context','alternatives':[]}
        except ValueError:pass
    if (slot in TEXT_SLOTS or (row and row.get('data_type')=='string' and row.get('allowed_values') in {'free_text','controlled_or_free_text'})) and len(clean)>1:
        return {'type':slot,'text':clean,'value':clean,'normalizedValue':clean,'normalizedId':None,
                'status':'resolved','method':'question_context','alternatives':[]}
    return None

def _fact(slot, entity, message_id, context):
    return {'id':str(uuid4()),'key':slot,'label':_label(context,slot),'value':entity['text'],
            'normalizedValue':entity.get('normalizedValue'),'normalizedId':entity.get('normalizedId'),
            'state':'provided','provenance':'USER_PROVIDED','confirmed':False,'requiresConfirmation':True,
            'sourceMessageId':message_id,'extractionMethod':entity.get('method'),
            'sourceText':entity['text'],'unit':entity.get('unit'),'approximate':entity.get('approximate'),'uncertainty':entity.get('uncertainty'),
            'resolutionStatus':entity.get('status','unresolved'),'updatedAt':now()}

def apply_answer(context, answer, question_id, message_id, reference_datetime=None):
    question=context.get('currentQuestion')
    if not question or question.get('id')!=question_id:raise ValueError('Question is stale or missing')
    if any(m['id']==message_id for m in context['messages']):raise ValueError('Duplicate answer')
    conv=state(context);target=question['slot'];clean=answer.strip()
    context['messages'].append({'id':message_id,'speaker':'user','text':clean})
    conv['lastAnswerLanguage']=analyze_language(clean,context['language'])
    detected=conv['lastAnswerLanguage']['detectedLanguage']
    if context['language']=='auto' and detected in {'english','hindi','hinglish'}:
        conv['displayLanguage']=detected
    context.pop('currentQuestion',None)
    if target in {'INTENT','INTENT_DOMAIN','INTENT_DETAIL'}:
        _resolve_intent(context,clean)
        label=next((o['label'] for o in question.get('options',[]) if o['value']==clean),None)
        if label is None and clean in ontology()['intents']:
            label=ontology()['intents'][clean]['intent_name'].replace('_',' ').title()
        conv.setdefault('intentAnswers',[]).append({'messageId':message_id,'value':clean})
        next(m for m in context['messages'] if m['id']==message_id)['text']=label or clean
        return recompute(context)
    if UNKNOWN.fullmatch(clean):
        if target not in conv['unknownSlots']:conv['unknownSlots'].append(target)
        context['answers'][target]=clean
        if any(c['slot']==target and not c.get('resolved') for c in conv['contradictions']):
            context['messages'].append({'id':f'conflict-help-{message_id}','speaker':'assistant',
                'text':'Two statements conflict. Please clarify or correct one before verification.'})
            context['currentQuestion']=question
        return recompute(context)
    existing_conflicts={c['id'] for c in conv['contradictions'] if not c.get('resolved')}
    entities, extraction_metadata=interpret(clean,reference_datetime,target_slot=target)
    conv.setdefault('extractionHistory',[]).append({'messageId':message_id,**extraction_metadata})
    if target=='LICENCE_CLASS':
        entities=[e for e in entities if not (e['type']=='VEHICLE_CLASS' and e['text'].casefold()==clean.casefold())]
    chosen=_target_entity(target,clean,entities,reference_datetime)
    candidate=next((f for f in context['facts'] if f['key']=='OBSERVED_SPEED' and f.get('unit')=='unknown'),None)
    if target=='OBSERVED_SPEED' and candidate and clean.casefold() in {'km/h','kmph','kph'}:
        chosen={'type':target,'text':candidate['value']+'; unit: '+clean,'value':candidate['normalizedValue'],
                'normalizedValue':candidate['normalizedValue'],'unit':'km/h','status':'resolved','method':'user_unit_confirmation',
                'normalizedId':None,'approximate':candidate.get('approximate'),'alternatives':[]}
        conv['factHistory'].append({'action':'confirm_speed_unit','previous':candidate.copy(),'at':now()})
    if target=='ROAD_TYPE' and chosen and chosen.get('normalizedValue')=='other' and chosen.get('method')!='question_context_allowed_value':
        if not any(e.get('type')=='LOCATION' and e.get('value','').casefold()==clean.casefold() for e in entities):
            entities.append({'type':'LOCATION','text':clean,'value':clean,'normalizedValue':clean,
                             'normalizedId':None,'status':'resolved','method':'preserved_road_context',
                             'alternatives':[]})
    if chosen and chosen not in entities:entities.append(chosen)
    for entity in entities:
        slot=target if entity is chosen else entity['type']
        incoming=_fact(slot,entity,message_id,context)
        prior=next((f for f in context['facts'] if f['key']==slot and (_has_value(f) or slot=='OBSERVED_SPEED' and f.get('normalizedValue'))),None)
        if prior and str(prior.get('normalizedValue') or prior['value']).casefold()!=str(incoming.get('normalizedValue') or incoming['value']).casefold():
            existing=next((c for c in conv['contradictions'] if c['slot']==slot and not c.get('resolved')),None)
            if existing:existing['candidate']=incoming
            else:conv['contradictions'].append({'id':str(uuid4()),'slot':slot,'previous':prior.copy(),
                'candidate':incoming,'kind':'possible_timeline' if TIMELINE.search(clean) else 'different_values',
                'resolved':False,'createdAt':now()})
            continue
        prior_mentions=[f for f in context['facts'] if f['key']==slot]
        if len(prior_mentions)>1:
            conv['factHistory'].append({'action':'resolve_multiple_mentions','previous':prior_mentions,'selected':incoming,'at':now()})
        context['facts']=[f for f in context['facts'] if f['key']!=slot]+[incoming]
        if slot in conv['unknownSlots']:conv['unknownSlots'].remove(slot)
        context['answers'][slot]=entity['text']
    # Only a question about an already-open contradiction selects a replacement.
    for conflict in conv['contradictions']:
        if conflict['id'] in existing_conflicts and conflict['slot']==target and not conflict.get('resolved') and chosen and chosen.get('status')=='resolved':
            replacement=_fact(target,chosen,message_id,context)
            conv['factHistory'].append({'action':'resolve_contradiction','previous':conflict['previous'],
                                        'candidate':conflict['candidate'],'selected':replacement,'at':now()})
            context['facts']=[f for f in context['facts'] if f['key']!=target]+[replacement]
            conflict['resolved']=True
    return recompute(context)

def revise_fact(context, fact_id, value):
    fact=next((f for f in context['facts'] if f['id']==fact_id),None)
    if not fact:raise KeyError(fact_id)
    entity=_target_entity(fact['key'],value,[normalize(e) for e in extract(value)])
    if entity is None or entity.get('status')!='resolved':raise ValueError('Could not normalize the corrected value')
    state(context)['factHistory'].append({'action':'edit','previous':fact.copy(),'at':now()})
    fact.update(value=value.strip(),normalizedValue=entity.get('normalizedValue'),normalizedId=entity.get('normalizedId'),
                state='provided',provenance='USER_PROVIDED',confirmed=False,requiresConfirmation=True,
                resolutionStatus='resolved',extractionMethod='user_correction',sourceText=value.strip(),
                unit=entity.get('unit'),approximate=entity.get('approximate'),uncertainty=None,updatedAt=now())
    for conflict in state(context)['contradictions']:
        if conflict['slot']==fact['key'] and not conflict.get('resolved'):conflict['resolved']=True
    context.pop('guidance',None);context.pop('verifiedAt',None)
    context.pop('currentQuestion',None)
    return recompute(context)

def confirm_fact(context, fact_id):
    fact=next((f for f in context['facts'] if f['id']==fact_id),None)
    if not fact:raise KeyError(fact_id)
    if not _has_value(fact):raise ValueError('Unresolved fact cannot be confirmed')
    if any(c['slot']==fact['key'] and not c.get('resolved') for c in state(context)['contradictions']):
        raise ValueError('Resolve the contradiction first')
    fact.update(state='confirmed',provenance='USER_CONFIRMED',confirmed=True,
                requiresConfirmation=False,updatedAt=now())
    return recompute(context)

def verify(context, acknowledge_unknowns=False):
    conv=state(context)
    blockers=[]
    if conv.get('intentUnsupported') or (context.get('nlpAnalysis',{}).get('intent',{}).get('needsClarification') and not conv.get('intentConfirmed')):
        blockers.append('A supported issue must be established before verification')
    if context.get('currentQuestion'):blockers.append('Follow-up question is still open')
    if any(not c.get('resolved') for c in conv['contradictions']):blockers.append('Contradictions remain')
    if set(conv.get('ambiguousSlots',[]))-set(conv['unknownSlots']):blockers.append('Ambiguous facts remain')
    missing=set(context['missingSlots'])
    if missing-set(conv['unknownSlots']):blockers.append('Required facts remain unanswered')
    if conv['unknownSlots'] and not acknowledge_unknowns:blockers.append('Acknowledge unknown facts')
    if any(f.get('requiresConfirmation') or not f.get('confirmed') for f in context['facts'] if _has_value(f)):
        blockers.append('Facts require individual confirmation')
    if blockers:return blockers
    conv['unknownsAcknowledged']=bool(conv['unknownSlots'])
    conv['verificationEligible']=True
    context['stage']='USER_VERIFIED';context['verifiedAt']=now()
    context['messages'].append({'id':str(uuid4()),'speaker':'assistant',
                                'text':'You verified the structured situation. Legal source checking has not started.'})
    return []
