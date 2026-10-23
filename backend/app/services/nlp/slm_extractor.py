"""SLM-only extractive interpretation. No legal assertions or model-authored facts."""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from threading import BoundedSemaphore
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.model_registry import MODELS, settings
from app.services.nlp.entity_extractor import SPEED
from app.services.nlp.normalizer import normalize
from app.services.nlp.ontology import ontology
from app.services.nlp.flexible_normalization import current_reference, state_candidate
from app.services.nlp.compact_intake import wire_schema, expand_response, wire_name

PROMPT_VERSION = 'intake-compact-v4'
_gate = BoundedSemaphore(1)

class IntakeFailure(RuntimeError):
    def __init__(self, reason, metadata):
        self.reason=reason
        self.metadata=metadata
        super().__init__('SLM interpretation could not complete ('+reason+'). Please retry; no rule-based extraction was used.')


class Mention(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    slot: str
    quote: str = Field(min_length=1, max_length=2000)
    value: str = Field(min_length=1, max_length=1000)
    certainty: Literal['clear', 'ambiguous', 'uncertain']
    approximate: bool


class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    facts: list[Mention] = Field(max_length=80)


def supported_slots():
    rows = {}
    for group in ontology()['slots'].values():
        for row in group:
            rows.setdefault(row['slot_name'], row)
    # Informational context only: NOT POLICE_REPORTED, a challan or an offence.
    rows['OBSERVED_SPEED_UNIT'] = {'data_type':'categorical','allowed_values':'km/h|mph'}
    rows['POLICE_INVOLVEMENT'] = {'data_type': 'string', 'allowed_values': 'free_text'}
    return rows


def _date(value, reference):
    numeric = re.fullmatch(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})', value)
    if numeric and int(numeric[1]) <= 12 and int(numeric[2]) <= 12 and numeric[1] != numeric[2]:
        return None  # Could be day/month or month/day: ask rather than guess.
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%d %B %Y', '%d %b %Y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    # General date normalization, not situation-specific extraction rules.
    offsets = {'today': 0, 'आज': 0, 'aaj': 0, 'yesterday': -1, 'बीता कल': -1,
               'बीते कल': -1, 'tomorrow': 1, 'aane wala kal': 1,
               'beeta kal': -1, 'pichle din': -1, 'कल': None, 'kal': None}
    key=value.casefold()
    if key not in offsets and len(key)>=5 and not any(c.isdigit() for c in key):
        ranked=sorted(((SequenceMatcher(None,key,k).ratio(),k) for k in offsets),reverse=True)
        if ranked[0][0]>=.88 and ranked[0][0]-ranked[1][0]>=.08:key=ranked[0][1]
    offset = offsets.get(key)
    if reference and reference.tzinfo and reference.utcoffset() is not None and offset is not None:
        return (reference.date() + timedelta(days=offset)).isoformat()
    return None


def validate_mentions(payload, text, reference=None):
    parsed = Extraction.model_validate_json(payload)
    slots = supported_slots()
    entities = []
    for fact in parsed.facts:
        if fact.slot=='OBSERVED_SPEED':
            speed_value=SPEED.fullmatch(fact.value)
            if speed_value:
                fact.approximate=fact.approximate or speed_value.group(0).casefold().startswith(('around','about','लगभग'))
                fact.value=speed_value.group('value')
        if fact.slot=='OBSERVED_SPEED' and fact.value.casefold() in {'km/h','kmph','kph','mph'}:
            fact.slot='OBSERVED_SPEED_UNIT'
        if fact.slot not in slots:
            raise ValueError('UNSUPPORTED_SLOT')
        # Exact evidence and extractive value prevent the model inventing a number,
        # date, normalized class, or categorical assertion absent from the message.
        if fact.quote not in text:
            match=re.search(re.escape(fact.quote),text,re.I)
            if match: fact.quote=match.group(0)
        if fact.value not in fact.quote:
            match=re.search(re.escape(fact.value),fact.quote,re.I)
            if match: fact.value=match.group(0)
        if fact.slot in {'STATE','DESTINATION_STATE'} and fact.quote in text and fact.value not in fact.quote:
            candidate=state_candidate(fact.quote)
            if candidate and candidate['state_ut_name'].casefold()==fact.value.casefold():
                fact.value=fact.quote
        if fact.slot.endswith('_DATE') and fact.quote not in text and len(fact.quote)>=5 and not any(c.isdigit() for c in fact.quote):
            # Recover a unique misspelled original date word; never alter numbers.
            ranked=sorted(((SequenceMatcher(None,fact.quote.casefold(),m.group().casefold()).ratio(),m.group()) for m in re.finditer(r'[^\W\d_]+',text)),reverse=True)
            if ranked and ranked[0][0]>=.88 and (len(ranked)==1 or ranked[0][0]-ranked[1][0]>=.08):
                if fact.value==fact.quote:fact.value=ranked[0][1]
                fact.quote=ranked[0][1]
        if fact.quote not in text or fact.value not in fact.quote:
            raise ValueError('UNGROUNDED_MENTION')
        start = text.index(fact.quote)
        entity = {'type': fact.slot, 'text': fact.quote, 'value': fact.value,
                  'start': start, 'end': start + len(fact.quote), 'method': 'local_slm_extractive',
                  'confidence': None}
        # Reuse vocabulary normalizers on the extracted value, preserving the
        # full supporting quote separately. Model cannot supply normalized IDs.
        probe = {**entity, 'text': fact.value}
        row = slots[fact.slot]
        if fact.slot == 'OBSERVED_SPEED':
            matches = list(SPEED.finditer(fact.quote))
            if not re.fullmatch(r'\d{1,3}', fact.value):
                raise ValueError('UNSUPPORTED_SPEED_VALUE')
        normalized = normalize(probe)
        normalized['interpretationNotes']=[]
        if fact.slot in {'STATE','DESTINATION_STATE'} and normalized['status']=='unresolved':
            candidate=state_candidate(fact.value)
            if candidate:
                normalized.update(normalizedValue=candidate['state_ut_name'],normalizedId=candidate['jurisdiction_id'],status='resolved',vocabularySource='jurisdiction catalog spelling normalization')
                normalized['interpretationNotes'].append('Read '+repr(fact.value)+' as '+candidate['state_ut_name']+'; please verify.')
        if fact.slot=='OBSERVED_SPEED_UNIT':
            unit={'km/h':'km/h','kmph':'km/h','kph':'km/h','mph':'mph'}.get(fact.value.casefold())
            if unit is None:raise ValueError('UNSUPPORTED_SPEED_UNIT')
            normalized.update(normalizedValue=unit,unit=unit,status='resolved')
        if fact.slot == 'OBSERVED_SPEED' and not matches:
            normalized.update(unit='unknown', status='unresolved', uncertainty='speed_unit_missing')
        if fact.slot == 'ROAD_TYPE' and normalized['normalizedValue'] not in {v.lower().replace('_',' ') for v in row['allowed_values'].split('|')} :
            normalized.update(normalizedValue='other', status='resolved', vocabularySource='unclassified road context')
        if row['data_type'] == 'string':
            normalized.update(normalizedValue=fact.value, status='resolved', vocabularySource='extractive user text')
        elif row['data_type'] == 'date':
            day = _date(fact.value, reference)
            normalized.update(normalizedValue=day, status='resolved' if day else 'unresolved')
        elif normalized['status'] == 'unresolved':
            # Only literal schema vocabulary is admissible here. Semantic
            # translations/guesses not handled by normalization need confirmation.
            allowed = {v.casefold().replace('_', ' '): v.casefold() for v in row['allowed_values'].split('|')}
            key = fact.value.casefold().replace('_', ' ')
            if key in allowed and key not in {'unknown', 'uncertain'}:
                normalized.update(normalizedValue=allowed[key], status='resolved', vocabularySource='slot_schema.csv literal value')
        speed_unit_missing = fact.slot == 'OBSERVED_SPEED' and not matches
        normalized.update(text=fact.quote, start=start, end=start + len(fact.quote),
                          approximate=fact.approximate, uncertainty=fact.certainty)
        if speed_unit_missing:
            normalized.update(unit='unknown', status='unresolved', uncertainty='speed_unit_missing')
        explicit_mph=bool(re.search(r'(?<!\w)mph(?!\w)',fact.quote,re.I) or re.match(r'\s*mph\b',text[start+len(fact.quote):],re.I))
        if speed_unit_missing and not explicit_mph and os.getenv('NYAYA_ASSUME_INDIAN_SPEED_KMPH','true').lower()=='true':
            normalized.update(unit='km/h',unitSource='context_default',status='resolved',uncertainty='unit_assumed_for_india')
            normalized['interpretationNotes'].append('Unit assumed: km/h for this India-focused app. You did not specify a unit; confirm or correct it during review.')
        elif fact.slot=='OBSERVED_SPEED':
            if explicit_mph:
                normalized.update(unit='mph',status='unresolved',uncertainty='unit_conversion_needs_confirmation')
            normalized['unitSource']='user_provided' if matches else 'unknown'
        if fact.slot == 'OBSERVED_SPEED':
            normalized['approximate'] = fact.approximate or any(
                m.group(0).casefold().startswith(('about', 'around', 'maybe', 'लगभग')) for m in matches)
        # Conservative assertion-scope guard. Exact quotations alone do not
        # establish that a negated or hypothetical statement actually happened.
        clause_prefix = re.split(r'[,;.!?।\n]', text[:start])[-1]
        clause_suffix = re.split(r'[,;.!?।\n]', text[start + len(fact.quote):])[0]
        if re.search(r"\b(?:not|never|if|might|maybe|nahi|agar)\b|n't\b|नहीं|अगर|शायद", clause_prefix + fact.quote + clause_suffix, re.I):
            normalized.update(status='unresolved', uncertainty='assertion_scope_needs_confirmation')
        normalized_primitive = (fact.slot=='OBSERVED_SPEED_UNIT' and normalized.get('unit') in {'km/h','mph'}) or (fact.slot=='OBSERVED_SPEED' and normalized.get('unitSource')=='context_default' and fact.certainty=='uncertain')
        if fact.certainty != 'clear' and not (normalized_primitive and normalized.get('uncertainty')!='assertion_scope_needs_confirmation') and not (row['data_type']=='date' and normalized.get('normalizedValue')) and not (fact.slot in {'STATE','DESTINATION_STATE'} and normalized.get('interpretationNotes')):
            normalized['status'] = 'ambiguous' if fact.certainty == 'ambiguous' else 'unresolved'
        if not any(e['type'] == normalized['type'] and e['text'] == normalized['text'] and e['value'] == normalized['value'] for e in entities):
            entities.append(normalized)
    return entities


def interpret(text, reference=None, *, provider=None, target_slot=None, context=None):
    if reference is None or reference.tzinfo is None or reference.utcoffset() is None:
        reference=current_reference()
    reference=reference.astimezone(timezone(timedelta(hours=5,minutes=30)))
    metadata = {'method': 'local_slm', 'fallbackUsed': False, 'promptVersion': PROMPT_VERSION,
                'modelCalled': False, 'referenceDatetime':reference.isoformat()}
    acquired = False
    try:
        if os.getenv('NYAYA_INTAKE_SLM_ENABLED', 'true').lower() != 'true':
            raise RuntimeFailure('INTAKE_SLM_DISABLED')
        config = settings()
        model_id = os.getenv('NYAYA_INTAKE_MODEL', config['default'])
        if model_id not in MODELS:
            raise ValueError('INVALID_INTAKE_MODEL')
        spec = MODELS[model_id]
        metadata.update(requestedModel=model_id, runtimeModel=spec.runtime_name, checkpoint=spec.checkpoint)
        timeout = max(1, min(float(os.getenv('NYAYA_INTAKE_TIMEOUT', '60')), 90))
        if len(text) > 16000:
            raise ValueError('INTAKE_CONTEXT_TOO_LARGE')
        # Queue briefly; contention produces an explicit retryable error.
        acquired = _gate.acquire(timeout=10)
        if not acquired:
            raise RuntimeFailure('INTAKE_BUSY')
        provider = provider or OllamaProvider(config['url'])
        available = provider.availability()['models'][model_id]
        if not available['available']:
            raise RuntimeFailure(available['status'].upper())
        rows = supported_slots()
        schema = wire_schema(rows,text,target_slot)
        # Compact context avoids replaying entire fact records and audit metadata.
        prior=[{'slot':f.get('key'),'value':f.get('normalizedValue') or f.get('value'),'unit':f.get('unit')}
               for f in (context or {}).get('facts',[])][:40]
        instruction=('Extract facts from the CURRENT user message. Return only JSON: facts maps field names to arrays of verbatim source text. Always include speed, state, date, road_type and vehicle; use an empty array [] if absent. Include other stated facts too; omit other absent fields. No assumptions or legal advice. '
            'speed = reported driving number with any stated units; state = Indian State/UT; date = date words exactly as written, including typos; road_type = road category; road_name = actual named road; vehicle = actual vehicle, never a road. '
            'location = place context; speed_unit = explicitly stated unit. Preserve negation, approximation and conflicting mentions. All field names: '+', '.join(wire_name(slot) for slot in rows))
        content=text
        if context or target_slot:
            content='conversationContext (background, not new facts): '+json.dumps({'answeringSlot':target_slot,'facts':prior},ensure_ascii=False)+'\nCURRENT message: '+text
        messages=[{'role':'system','content':instruction},{'role':'user','content':content}]
        max_tokens=640 if len(text)<=200 else 1400
        metadata['modelCalled'] = True
        metadata['generationParameters'] = {'temperature': 0, 'maxTokens': max_tokens, 'timeoutSeconds': timeout}
        response = provider.generate(spec.runtime_name, messages, temperature=0, max_tokens=max_tokens,
                                     timeout=timeout, output_schema=schema)
        payload=Extraction.model_validate(expand_response(response.text))
        entities=[]
        rejected=[]
        for mention in payload.facts:
            try:
                entities.extend(validate_mentions(json.dumps({'facts':[mention.model_dump()]},ensure_ascii=False),text,reference))
            except ValueError as exc:
                rejected.append({'slot':mention.slot,'quote':mention.quote,'reason':str(exc)[:200]})
        metadata['rejectedMentions']=rejected
        if payload.facts and not entities:
            raise ValueError('NO_GROUNDED_FACTS: '+','.join(r['reason'] for r in rejected))
        unassigned=[e for e in entities if e.get('uncertainty')=='uncertain' and not e.get('interpretationNotes') and rows[e['type']]['data_type']=='categorical' and e['type']!=target_slot and e['type']!='OBSERVED_SPEED_UNIT']
        metadata['unassignedMentions']=unassigned
        entities=[e for e in entities if e not in unassigned]
        if target_slot=='ROAD_TYPE':
            for entity in entities:
                if entity['type']=='ROAD_TYPE' and entity.get('normalizedValue')=='other' and entity.get('uncertainty')!='assertion_scope_needs_confirmation':
                    entity.update(status='resolved',uncertainty='road_category_unspecified')
        if target_slot=='ROAD_TYPE' and not any(e['type']=='ROAD_TYPE' for e in entities):
            contextual=next((e for e in entities if e['type']=='LOCATION' and e['status']=='resolved'),None)
            if contextual:
                entities.append({**contextual,'type':'ROAD_TYPE','normalizedValue':'other',
                    'vocabularySource':'unspecified road category; location context preserved'})
        for entity in list(entities):
            if entity['type']=='ROAD_TYPE' and entity.get('normalizedValue')=='other' and entity['status']=='resolved':
                if not any(e['type']=='LOCATION' and e['text']==entity['text'] for e in entities):
                    entities.append({**entity,'type':'LOCATION','normalizedValue':entity['value'],
                        'vocabularySource':'original unclassified road context'})
        metadata.update(method='local_slm', fallbackUsed=False, latencyMs=response.duration_ms,
                        installedDigest=available.get('digest'), entityCount=len(entities),
                        promptTokens=response.prompt_tokens, outputTokens=response.output_tokens)
        return entities, metadata
    except (RuntimeFailure, ValueError, KeyError, TypeError, AttributeError) as exc:
        metadata['failureReason'] = str(exc)[:300]
        metadata['method']='local_slm_failed'
        raise IntakeFailure(metadata['failureReason'],metadata) from exc
    finally:
        if acquired:
            _gate.release()
