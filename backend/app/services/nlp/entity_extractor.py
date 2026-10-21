"""Rule-based span extractor on original text; this is not trained NER."""
import re
import json
import csv
from functools import lru_cache
from datetime import datetime,timedelta
from app.services.nlp.ontology import ontology
from app.services.nlp.jurisdiction_aliases import STATE_ALIASES
from app.config import DATASET_DIR, BACKEND_DIR
from app.services.dataset_loader import load_dataset

SPEED=re.compile(r'(?<!\w)(?:(?:about|around|maybe|लगभग)\s+)?(?P<value>\d{2,3})\s*(?P<unit>km\s*/\s*h|kmph|kph|किमी\s*/\s*घंटा|किलोमीटर\s+प्रति\s+घंटा)(?!\w)',re.I)
DATE_ISO=re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
DATE_WORD=re.compile(r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',re.I)
ROAD=re.compile(r'\b(?:expressway|national highway|state highway|service road|parking area|city road|highway|motorway|village road|residential road|urban road)\b|एक्सप्रेसवे|हाईवे|राजमार्ग',re.I)
VEHICLES=re.compile(r'(?<!\w)(?:auto[- ]rickshaw|e[- ]rickshaw|(?:motorcycle|bike|scooter)\s+(?:with(?:out)?\s+gears?|gearless)|(?:geared|gearless)\s+(?:motorcycle|bike|scooter)|MCWOG|MCWG|motorcycle|scooter|bike|car|bus|truck|lorry|motor car|मोटरसाइकिल|बाइक|स्कूटर|कार|बस)(?!\w)',re.I)
INSURANCE=re.compile(r'\b(?:insurance|policy)\b.{0,24}\b(?:expired|valid|active|lapsed)\b|\b(?:no|without)\s+insurance\b|बीमा.{0,15}(?:खत्म|समाप्त|वैध)|\binsurance\s+expire(?:d)?\s+ho\s+gaya\b',re.I)
CHALLAN=re.compile(r'\b(?:did not receive|didn.t get|no|without)\s+(?:a\s+)?challan\b|\b(?:received|got|issued|paid)\s+(?:a\s+)?challan\b|चालान.{0,15}(?:नहीं|कटा|मिला)|\bchallan\s+kat\s+gaya\b',re.I)
LICENCE=re.compile(r'\b(?:licen[cs]e|dl)\b.{0,20}\b(?:expired|valid|suspended|seized)\b|\b(?:no|without)\s+(?:driving\s+)?licen[cs]e\b',re.I)
AGE=re.compile(r'\b(?P<age>\d{1,2})\s*(?:years? old|yrs? old|साल)\b',re.I)
AGE_SELF=re.compile(r'\bI\s+am\s+(?P<age>\d{1,2})(?!\d)(?!\s*(?:km|years? of experience))',re.I)
AGE_LABEL=re.compile(r'(?:\bage\b|उम्र)\s*[:：-]\s*(?P<age>\d{1,2})',re.I)

@lru_cache(maxsize=1)
def status_vocabulary():
    """Only training annotations may supply status phrases used at inference."""
    manifest=BACKEND_DIR/'experiments'/'manifests'/'phase6_grouped_split.csv'
    if not manifest.is_file():
        raise FileNotFoundError('Prepare the NLP training split before entity inference')
    with manifest.open(encoding='utf-8',newline='') as stream:
        allowed={row['utterance_id'] for row in csv.DictReader(stream) if row['split']=='train'}
    return build_status_vocabulary(allowed)


def build_status_vocabulary(allowed_ids):
    """Create a vocabulary from a specified training fold only."""
    values={kind:set() for kind in ('CHALLAN_STATUS','LICENCE_STATUS','INSURANCE_STATUS')}
    _,rows=load_dataset(DATASET_DIR/'annotated_utterances.csv')
    for _,row in rows:
        if not isinstance(row,dict) or row.get('utterance_id') not in allowed_ids:continue
        try: annotations=json.loads(row.get('entity_annotations_json') or '[]')
        except json.JSONDecodeError:continue
        for item in annotations:
            if isinstance(item,dict) and item.get('slot_name') in values and isinstance(item.get('value'),str):
                values[item['slot_name']].add(item['value'].casefold())
    return {kind:sorted(items,key=len,reverse=True) for kind,items in values.items()}


def extract(text: str, reference_datetime: datetime | None=None, status_values=None):
    entities=[]
    def add(kind,match,value=None,method='rule'):
        entities.append({'type':kind,'text':match.group(0),'value':value or match.group(0),
                         'start':match.start(),'end':match.end(),'method':method,'confidence':None})
    for m in SPEED.finditer(text): add('OBSERVED_SPEED',m,m.group('value'))
    # Explicit noun/status pairs are clause-scoped; unrelated documents cannot lend a status.
    document_names={
        'INSURANCE_STATUS':r'insurance|policy|बीमा',
        'LICENCE_STATUS':r'(?:driving\s+)?licen[cs]e|(?:ड्राइविंग\s+)?लाइसेंस',
        'PUC_STATUS':r'(?:pollution|PUC)\s*(?:certificate)?|प्रदूषण प्रमाणपत्र',
        'PERMIT_STATUS':r'permit|परमिट', 'FITNESS_STATUS':r'fitness certificate|फिटनेस प्रमाणपत्र',
    }
    status_words={'expired':r'expired|lapsed|over|एक्सपायर|समाप्त|खत्म',
                  'valid':r'valid|वैध', 'active':r'active', 'suspended':r'suspended|निलंबित', 'seized':r'seized|जब्त'}
    for kind,nouns in document_names.items():
        for status,words in status_words.items():
            pattern=r'(?<!\w)(?:'+nouns+r')(?!\w)[^,;.!?।\n]{0,35}?(?P<status>(?<!\w)(?:'+words+r')(?!\w))'
            for m in re.finditer(pattern,text,re.I):
                # Preserve explicit negation as unresolved rather than reversing its meaning.
                prefix=text[m.start():m.start('status')]
                if re.search(r'\b(?:claim|application|request|appeal)\b',prefix,re.I):continue
                negated=bool(re.search(r"\b(?:not|no|never)\b|नहीं",prefix,re.I))
                entities.append({'type':kind,'text':m.group(0),'value':status,'start':m.start(),'end':m.end(),
                                 'method':'negated_document_status' if negated else 'explicit_document_status','confidence':None})

    for m in VEHICLES.finditer(text): add('VEHICLE_CLASS',m)
    vehicle_names={r[key] for r in ontology()['vehicles'].values() for key in ('vehicle_class_id','legal_vehicle_code','common_name') if r.get(key)}
    pattern=r'(?<!\w)(?:'+'|'.join(re.escape(n) for n in sorted(vehicle_names,key=len,reverse=True))+r')(?!\w)'
    for m in re.finditer(pattern,text,re.I):
        entities[:]=[e for e in entities if not (e['type']=='VEHICLE_CLASS' and e['start']>=m.start() and e['end']<=m.end())]
        add('VEHICLE_CLASS',m,method='ontology_vehicle_name')
    for m in ROAD.finditer(text): add('ROAD_TYPE',m)
    for m in DATE_ISO.finditer(text): add('EVENT_DATE',m)
    for m in DATE_WORD.finditer(text): add('EVENT_DATE',m)
    if reference_datetime:
        for m in re.finditer(r'\b(?:yesterday|today)\b|\b(?:कल|आज)\b',text,re.I):
            token=m.group(0).casefold()
            if token in {'yesterday','today','आज'}:
                day=(reference_datetime.date()-timedelta(days=1)) if token=='yesterday' else reference_datetime.date()
                add('EVENT_DATE',m,day.isoformat(),'relative_date')
            # Hindi कल can mean yesterday or tomorrow, so leave unresolved.
            else:add('EVENT_DATE',m,method='ambiguous_relative_date')
    for m in INSURANCE.finditer(text): add('INSURANCE_STATUS',m)
    for m in CHALLAN.finditer(text): add('CHALLAN_STATUS',m)
    for m in LICENCE.finditer(text): add('LICENCE_STATUS',m)
    for m in AGE.finditer(text): add('AGE',m,m.group('age'))
    for m in list(AGE_LABEL.finditer(text))+list(AGE_SELF.finditer(text)):
        if not any(e['type']=='AGE' and e['start']<=m.start('age')<e['end'] for e in entities):
            entities.append({'type':'AGE','text':m.group('age'),'value':m.group('age'),
                             'start':m.start('age'),'end':m.end('age'),'method':'rule','confidence':None})
    cues={'CHALLAN_STATUS':r'challan|चालान','LICENCE_STATUS':r'licen[cs]e|\bdl\b|लाइसेंस',
          'INSURANCE_STATUS':r'insurance|policy|बीमा'}
    for kind,phrases in (status_values if status_values is not None else status_vocabulary()).items():
        for phrase in phrases:
            for m in re.finditer(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',text,re.I):
                vicinity=re.split(r'[,;.!?।]',text[:m.start()])[-1][-45:]+m.group(0)+re.split(r'[,;.!?।]',text[m.end():])[0][:45]
                if not re.search(cues[kind],vicinity,re.I):continue
                if any(e['type']==kind and e['start']<=m.start()<e['end'] for e in entities):continue
                entities.append({'type':kind,'text':m.group(0),'value':m.group(0),
                                 'start':m.start(),'end':m.end(),'method':'annotation_vocabulary','confidence':None})
    for m in re.finditer(r'\b(?:nobody|no one)\s+(?:was|is|got)\s+injured\b|\bno\s+injuries\b',text,re.I):
        entities.append({'type':'INJURY_PRESENT','text':m.group(0),'value':'no','start':m.start(),'end':m.end(),
                         'method':'explicit_schema_label','confidence':None})
    for m in re.finditer(r'\b(?:is|are|was|were|am|got)\s+(?:(?:seriously|badly|slightly)\s+)?(?:injured|bleeding|hurt|unconscious)\b',text,re.I):
        prefix=re.split(r'[.!?;।,]',text[:m.start()])[-1]
        if re.search(r"\b(?:not|no|nobody|no one|if|unless|whether)\b",prefix,re.I):continue
        entities.append({'type':'INJURY_PRESENT','text':m.group(0),'value':'yes','start':m.start(),'end':m.end(),
                         'method':'explicit_schema_label','confidence':None})
    # Match only dataset jurisdiction names and a few documented, unambiguous spellings.
    names={r['state_ut_name'].casefold():r['state_ut_name'] for r in ontology()['jurisdictions'].values() if r['jurisdiction_level']!='CENTRAL'}
    names['tamilnadu']='Tamil Nadu'
    names.update(STATE_ALIASES)
    for name in sorted(names,key=len,reverse=True):
        for m in re.finditer(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text,re.I):
            if not any(e['type']=='STATE' and e['start']<=m.start()<e['end'] for e in entities):
                add('STATE',m)
    # Explicit labelled facts use the schema vocabulary, never evaluation examples.
    # Labels scope shared values such as "valid" or "yes" to their own slot.
    labels={
        'LICENCE_CLASS':['license class','लाइसेंस वर्ग','लाइसेंस श्रेणी'],
        'USER_ROLE':['your role','आपकी भूमिका'], 'EVENT_DATE':['date','तारीख'],
        'CHALLAN_DATE':['challan date','चालान की तारीख'], 'RC_STATUS':['RC status','आरसी की स्थिति'],
        'INJURY_PRESENT':['injury status','चोट की स्थिति'], 'DEATH_PRESENT':['death status','मृत्यु की स्थिति'],
        'INSURANCE_STATUS':['बीमा की स्थिति'], 'LICENCE_STATUS':['लाइसेंस की स्थिति'],
        'POLICE_REPORTED':['police reported','पुलिस रिपोर्ट'], 'CITY':['शहर'],
    }
    names_of_states={r['state_ut_name'] for r in ontology()['jurisdictions'].values() if r['jurisdiction_level']!='CENTRAL'} | {'Tamilnadu'}
    configured={row['slot_name']:row for group in ontology()['slots'].values() for row in group}
    for slot,row in configured.items():
        names={row['slot_display_name'],slot.replace('_',' '),*labels.get(slot,[])}
        pattern=r'(?<!\w)(?:'+'|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True))+r')\s*[:：]\s*(?P<value>[^,;।\n]+)'
        for m in re.finditer(pattern,text,re.I):
            raw=m.group('value').strip().rstrip('.!?')
            if not raw:continue
            start=m.start('value')+len(m.group('value'))-len(m.group('value').lstrip())
            end=start+len(raw)
            if any(e['type']==slot and e['start']<=start and e['end']>=end for e in entities):continue
            allowed=row['allowed_values'].split('|')
            if row['data_type']=='categorical' and len(allowed)>1:
                candidates=sorted(set(allowed+['vehicle '+v.replace('_',' ') for v in allowed] if slot=='USER_ROLE' else allowed),key=len,reverse=True)
                matched=next((v for v in candidates if re.match(re.escape(v.replace('_',' '))+r'(?!\w)',raw,re.I)),None)
                if not matched:continue
                raw=raw[:len(matched.replace('_',' '))];end=start+len(raw)
            elif row['allowed_values']=='INDIAN_STATE_OR_UT':
                matches=[name for name in names_of_states if re.match(re.escape(name)+r'(?!\w)',raw,re.I)]
                if not matches:continue
                raw=raw[:len(max(matches,key=len))];end=start+len(raw)
            elif row['data_type']=='date':
                date_match=DATE_ISO.match(raw) or DATE_WORD.match(raw)
                if not date_match:continue
                raw=date_match.group();end=start+len(raw)
            elif row['data_type']!='string':continue
            entities.append({'type':slot,'text':text[start:end],'value':raw,'start':start,'end':end,
                             'method':'explicit_schema_label','confidence':None})
    for m in re.finditer(r'\bI\s+am\s+(?:the\s+|a\s+)?(?P<role>registered owner|driver|owner|buyer|seller|passenger|victim|witness|operator|applicant)\b',text,re.I):
        entities.append({'type':'USER_ROLE','text':m.group('role'),'value':m.group('role'),
                         'start':m.start('role'),'end':m.end('role'),'method':'explicit_role','confidence':None})
    # A licence entitlement code is not evidence of the incident vehicle class.
    licence_spans=[e for e in entities if e['type']=='LICENCE_CLASS']
    entities=[e for e in entities if not (e['type']=='VEHICLE_CLASS' and any(
        x['start']<=e['start'] and e['end']<=x['end'] for x in licence_spans))]
    # A negated vehicle mention is not a candidate replacement in a correction.
    entities=[e for e in entities if not (e['type']=='VEHICLE_CLASS' and re.search(
        r'\bnot\s+(?:(?:a|the|my)\s+)?$',text[max(0,e['start']-18):e['start']],re.I))]
    for m in re.finditer(r'\bI\s+(?:was\s+driving|am\s+driving|drive|drove)\b',text,re.I):
        entities.append({'type':'USER_ROLE','text':m.group(0),'value':'driver','start':m.start(),'end':m.end(),
                         'method':'explicit_role','confidence':None})
    explicit=[e for e in entities if e['method'] in {'explicit_document_status','negated_document_status'}]
    entities=[e for e in entities if e in explicit or not any(
        e['type']==x['type'] and x['start']<=e['start'] and e['end']<=x['end'] for x in explicit)]
    for m in re.finditer(r'\bI\s+(?:saw|witnessed)\b',text,re.I):
        entities.append({'type':'USER_ROLE','text':m.group(0),'value':'witness','start':m.start(),'end':m.end(),
                         'method':'explicit_role','confidence':None})
    entities.sort(key=lambda e:(e['start'],e['end'],e['type']))
    return entities
