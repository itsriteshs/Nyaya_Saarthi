"""Rule-based span extractor on original text; this is not trained NER."""
import re
import json
import csv
from functools import lru_cache
from datetime import datetime,timedelta
from app.services.nlp.ontology import ontology
from app.config import DATASET_DIR, BACKEND_DIR
from app.services.dataset_loader import load_dataset

SPEED=re.compile(r'(?<!\w)(?:(?:about|around|maybe|लगभग)\s+)?(?P<value>\d{2,3})\s*(?P<unit>km\s*/\s*h|kmph|kph|किमी\s*/\s*घंटा)(?!\w)',re.I)
DATE_ISO=re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
DATE_WORD=re.compile(r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',re.I)
ROAD=re.compile(r'\b(?:expressway|national highway|state highway|service road|parking area|city road|highway|motorway|village road|residential road|urban road)\b|एक्सप्रेसवे|हाईवे|राजमार्ग',re.I)
VEHICLES=re.compile(r'(?<!\w)(?:auto[- ]rickshaw|e[- ]rickshaw|(?:motorcycle|bike|scooter)\s+(?:with(?:out)?\s+gears?|gearless)|(?:geared|gearless)\s+(?:motorcycle|bike|scooter)|MCWOG|MCWG|motorcycle|scooter|bike|car|bus|truck|lorry|motor car|मोटरसाइकिल|स्कूटर|कार|बस)(?!\w)',re.I)
INSURANCE=re.compile(r'\b(?:insurance|policy)\b.{0,24}\b(?:expired|valid|active|lapsed)\b|\b(?:no|without)\s+insurance\b|बीमा.{0,15}(?:खत्म|समाप्त|वैध)|\binsurance\s+expire(?:d)?\s+ho\s+gaya\b',re.I)
CHALLAN=re.compile(r'\b(?:did not receive|didn.t get|no|without)\s+(?:a\s+)?challan\b|\b(?:received|got|issued|paid)\s+(?:a\s+)?challan\b|चालान.{0,15}(?:नहीं|कटा|मिला)|\bchallan\s+kat\s+gaya\b',re.I)
LICENCE=re.compile(r'\b(?:licen[cs]e|dl)\b.{0,20}\b(?:expired|valid|suspended|seized)\b|\b(?:no|without)\s+(?:driving\s+)?licen[cs]e\b',re.I)
AGE=re.compile(r'\b(?P<age>\d{1,2})\s*(?:years? old|yrs? old|साल)\b',re.I)
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
    for m in VEHICLES.finditer(text): add('VEHICLE_CLASS',m)
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
    for m in AGE_LABEL.finditer(text):
        if not any(e['type']=='AGE' and e['start']<=m.start('age')<e['end'] for e in entities):
            entities.append({'type':'AGE','text':m.group('age'),'value':m.group('age'),
                             'start':m.start('age'),'end':m.end('age'),'method':'rule','confidence':None})
    cues={'CHALLAN_STATUS':r'challan|चालान','LICENCE_STATUS':r'licen[cs]e|\bdl\b|लाइसेंस',
          'INSURANCE_STATUS':r'insurance|policy|बीमा'}
    for kind,phrases in (status_values if status_values is not None else status_vocabulary()).items():
        for phrase in phrases:
            for m in re.finditer(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',text,re.I):
                vicinity=text[max(0,m.start()-45):min(len(text),m.end()+45)]
                if not re.search(cues[kind],vicinity,re.I):continue
                if any(e['type']==kind and e['start']<=m.start()<e['end'] for e in entities):continue
                entities.append({'type':kind,'text':m.group(0),'value':m.group(0),
                                 'start':m.start(),'end':m.end(),'method':'annotation_vocabulary','confidence':None})
    # Match only dataset jurisdiction names and a few documented, unambiguous spellings.
    names={r['state_ut_name'].casefold():r['state_ut_name'] for r in ontology()['jurisdictions'].values() if r['jurisdiction_level']!='CENTRAL'}
    names['tamilnadu']='Tamil Nadu'
    for name in sorted(names,key=len,reverse=True):
        for m in re.finditer(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text,re.I):
            if not any(e['type']=='STATE' and e['start']<=m.start()<e['end'] for e in entities):
                add('STATE',m)
    # Explicit labelled facts use the schema vocabulary, never evaluation examples.
    # Labels scope shared values such as "valid" or "yes" to their own slot.
    labels={
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
    entities.sort(key=lambda e:(e['start'],e['end'],e['type']))
    return entities
