"""Deterministic, dataset-driven conversation state on the existing matter record."""
from datetime import datetime, timezone
import json
import re
from uuid import uuid4
from app.services.nlp.ontology import ontology
from app.services.nlp.entity_extractor import extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.language import analyze_language

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
    return sorted(ontology()['slots'].get(intent,[]),key=lambda r:(int(r['ask_priority'] or 999),r['slot_id']))

def _label(context, slot):
    return next((r['slot_display_name'] for r in _rows(context) if r['slot_name']==slot),slot.replace('_',' ').title())

def _question(context, slot, reason='missing'):
    row=next((r for r in _rows(context) if r['slot_name']==slot),None)
    lang=state(context)['displayLanguage']
    column={'hindi':'question_template_hi','hinglish':'question_template_hinglish'}.get(lang,'question_template_en')
    template=(row or {}).get(column) or (row or {}).get('question_template_en') or f'Please clarify {_label(context,slot)}.'
    if reason=='contradiction':
        template=f"Two answers about {_label(context,slot)} differ. Which describes the event? {template}"
    return {'id':f"q-{slot}-{len(state(context)['askedSlots'])+1}", 'slot':slot,'question':template,
            'type':'text','why':(row or {}).get('why_legally_relevant') or 'This detail helps establish the context.'}

def _has_value(fact):
    return fact.get('state') != 'unknown' and fact.get('resolutionStatus','resolved') == 'resolved' and bool(fact.get('normalizedValue') or fact.get('value'))

def recompute(context):
    """Only required/intent-context schema rows block completeness; unsupported conditions stay visible."""
    conv=state(context)
    facts={f['key']:f for f in context.get('facts',[]) if _has_value(f)}
    conflicted={c['slot'] for c in conv['contradictions'] if not c.get('resolved')}
    ambiguous={f['key'] for f in context.get('facts',[]) if f.get('resolutionStatus') in {'ambiguous','unresolved'}}
    conv['ambiguousSlots']=sorted(ambiguous)
    missing=[];unresolved=[];found=total=0
    for row in _rows(context):
        slot=row['slot_name'];level=row['required_level']
        try:condition=json.loads(row.get('required_when_json') or '{}').get('when')
        except json.JSONDecodeError:condition='invalid_json'
        if level=='required' and condition=='intent_context':
            total+=1
            if slot in facts and slot not in conflicted:found+=1
            else:missing.append(slot)
        elif level=='conditional':
            unresolved.append({'slot':slot,'condition':condition,'reason':'condition_not_implemented'})
        elif level!='optional':
            unresolved.append({'slot':slot,'condition':condition,'reason':'unsupported_requirement'})
    if context.get('nlpAnalysis',{}).get('intent',{}).get('id')=='INT016':
        unresolved.append({'slot':'AGE','condition':'schema_missing','reason':'provisional_schema_gap'})
    conv['unresolvedRequirements']=unresolved
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

def initialize(context):
    conv=state(context);conv['displayLanguage']=_language(context)
    conv['urgentAssistance']=bool(re.search(r'(?:injur(?:y|ed)|घायल|serious accident|गंभीर दुर्घटना)',context['originalText'],re.I))
    for index,fact in enumerate(context['facts']):
        entity=context['nlpAnalysis']['entities'][index]
        fact.update(normalizedValue=entity.get('normalizedValue'),normalizedId=entity.get('normalizedId'),
                    sourceMessageId='user-initial',extractionMethod=entity.get('method'),
                    resolutionStatus=entity['status'],updatedAt=now())
    first_by_slot={}
    for fact in context['facts']:
        if not _has_value(fact):continue
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

def _target_entity(slot, answer, entities):
    matches=[e for e in entities if e['type']==slot]
    if slot=='CHALLAN_DATE': matches=[e for e in entities if e['type']=='EVENT_DATE']
    if matches:return matches[0]
    clean=answer.strip()
    row=next((r for group in ontology()['slots'].values() for r in group if r['slot_name']==slot),None)
    if row and row.get('data_type')=='categorical':
        allowed={value.casefold().replace('_',' '):value.casefold() for value in row.get('allowed_values','').split('|')}
        matched=allowed.get(clean.casefold().replace('_',' '))
        if matched and matched!='unknown':
            return {'type':slot,'text':clean,'value':clean,'normalizedValue':matched,'normalizedId':None,
                    'status':'resolved','method':'question_context_allowed_value','alternatives':[]}
    if slot=='OBSERVED_SPEED':
        match=re.fullmatch(r'(?:about|around|maybe|लगभग)?\s*(\d{1,3})(?:\s*(?:km/h|kmph|kph))?',clean,re.I)
        if match:return {'type':slot,'text':clean,'value':match.group(1),'normalizedValue':match.group(1),
                         'normalizedId':None,'status':'resolved','method':'question_context','alternatives':[]}
    if slot in BOOL_SLOTS and (POSITIVE.fullmatch(clean) or NEGATIVE.fullmatch(clean)):
        return {'type':slot,'text':clean,'value':clean,'normalizedValue':'yes' if POSITIVE.fullmatch(clean) else 'no',
                'normalizedId':None,'status':'resolved','method':'question_context','alternatives':[]}
    if slot in DATE_SLOTS:
        from datetime import date
        try:
            value=date.fromisoformat(clean).isoformat()
            return {'type':slot,'text':clean,'value':clean,'normalizedValue':value,'normalizedId':None,
                    'status':'resolved','method':'question_context','alternatives':[]}
        except ValueError:pass
    if slot in TEXT_SLOTS and len(clean)>1:
        return {'type':slot,'text':clean,'value':clean,'normalizedValue':clean,'normalizedId':None,
                'status':'resolved','method':'question_context','alternatives':[]}
    return None

def _fact(slot, entity, message_id, context):
    return {'id':str(uuid4()),'key':slot,'label':_label(context,slot),'value':entity['text'],
            'normalizedValue':entity.get('normalizedValue'),'normalizedId':entity.get('normalizedId'),
            'state':'provided','provenance':'USER_PROVIDED','confirmed':False,'requiresConfirmation':True,
            'sourceMessageId':message_id,'extractionMethod':entity.get('method'),
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
    if UNKNOWN.fullmatch(clean):
        if target not in conv['unknownSlots']:conv['unknownSlots'].append(target)
        context['answers'][target]=clean
        if any(c['slot']==target and not c.get('resolved') for c in conv['contradictions']):
            context['messages'].append({'id':f'conflict-help-{message_id}','speaker':'assistant',
                'text':'Two statements conflict. Please clarify or correct one before verification.'})
            context['currentQuestion']=question
        return recompute(context)
    entities=[normalize(e) for e in extract(clean,reference_datetime)]
    chosen=_target_entity(target,clean,entities)
    if chosen and chosen.get('status')!='resolved':
        context['messages'].append({'id':f'clarify-{message_id}','speaker':'assistant',
            'text':f'{_label(context,target)} is ambiguous. Please provide a more specific answer.'})
        context['currentQuestion']=question
        return recompute(context)
    if chosen and chosen not in entities:entities.append(chosen)
    if not chosen:
        context['messages'].append({'id':f'help-{message_id}','speaker':'assistant',
                                    'text':f'I could not identify {_label(context,target)} in that answer. Please try a clearer value or say you do not know.'})
        context['currentQuestion']=question
        return recompute(context)
    for entity in entities:
        slot=target if entity is chosen else entity['type']
        if slot not in {r['slot_name'] for r in _rows(context)} and slot!=target:continue
        if entity.get('status')!='resolved':continue
        incoming=_fact(slot,entity,message_id,context)
        prior=next((f for f in context['facts'] if f['key']==slot and _has_value(f)),None)
        if prior and str(prior.get('normalizedValue') or prior['value']).casefold()!=str(incoming.get('normalizedValue') or incoming['value']).casefold():
            existing=next((c for c in conv['contradictions'] if c['slot']==slot and not c.get('resolved')),None)
            if existing:existing['candidate']=incoming
            else:conv['contradictions'].append({'id':str(uuid4()),'slot':slot,'previous':prior.copy(),
                'candidate':incoming,'kind':'possible_timeline' if TIMELINE.search(clean) else 'different_values',
                'resolved':False,'createdAt':now()})
            continue
        context['facts']=[f for f in context['facts'] if f['key']!=slot]+[incoming]
        if slot in conv['unknownSlots']:conv['unknownSlots'].remove(slot)
        context['answers'][slot]=entity['text']
    # A response to a contradiction question explicitly selects a replacement.
    for conflict in conv['contradictions']:
        if conflict['slot']==target and not conflict.get('resolved') and chosen.get('status')=='resolved':
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
                resolutionStatus='resolved',extractionMethod='user_correction',updatedAt=now())
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
