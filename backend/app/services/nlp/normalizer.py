"""Ground entity normalization in vehicle and jurisdiction CSV vocabularies."""
from datetime import date,datetime
import re
from app.services.nlp.ontology import ontology

VEHICLE_ALIASES={
    'car':['VC_MOTORCAR'],'motor car':['VC_MOTORCAR'],'कार':['VC_MOTORCAR'],
    'auto-rickshaw':['VC_THREE_WHEELER_TRANSPORT'],'auto rickshaw':['VC_THREE_WHEELER_TRANSPORT'],
    'e-rickshaw':['VC_E_RICKSHAW'],
    'bike':['VC_MCWG','VC_MCWOG'],'motorcycle':['VC_MCWG','VC_MCWOG'],
    'मोटरसाइकिल':['VC_MCWG','VC_MCWOG'],'scooter':['VC_MCWG','VC_MCWOG'],'स्कूटर':['VC_MCWG','VC_MCWOG'],
    'bus':['VC_OMNIBUS','VC_MPV','VC_HPMV'],'बस':['VC_OMNIBUS','VC_MPV','VC_HPMV'],
    'truck':['VC_MGV','VC_HGV'],'lorry':['VC_MGV','VC_HGV'],
}

def normalize(entity):
    e=dict(entity);kind=e['type'];raw=e['text'];value=str(e['value'])
    e.update({'normalizedValue':None,'normalizedId':None,'status':'unresolved','vocabularySource':None,'alternatives':[]})
    if kind=='OBSERVED_SPEED':
        e.update(normalizedValue=str(int(value)),unit='km/h',status='resolved',vocabularySource='unit pattern')
        e['approximate']=any(x in raw.lower() for x in ('about','around','maybe','लगभग'))
    elif kind=='VEHICLE_CLASS':
        options=[x for x in VEHICLE_ALIASES.get(raw.casefold(),[]) if x in ontology()['vehicles']]
        e['alternatives']=options
        if len(options)==1:e.update(normalizedValue=ontology()['vehicles'][options[0]]['common_name'],normalizedId=options[0],status='resolved')
        elif options:e.update(normalizedValue='Vehicle class needs clarification',status='ambiguous')
        e['vocabularySource']='vehicle_classes.csv + documented informal aliases'
    elif kind in {'STATE','DESTINATION_STATE'}:
        lookup={r['state_ut_name'].casefold():r for r in ontology()['jurisdictions'].values() if r['jurisdiction_level']!='CENTRAL'}
        key=raw.casefold().replace('tamilnadu','tamil nadu')
        if key in lookup:e.update(normalizedValue=lookup[key]['state_ut_name'],normalizedId=lookup[key]['jurisdiction_id'],status='resolved')
        e['vocabularySource']='jurisdictions.csv'
    elif kind.endswith('_DATE'):
        try:
            if e['method']=='ambiguous_relative_date':return e
            if e['method']=='relative_date':day=date.fromisoformat(value)
            else:
                try:day=date.fromisoformat(raw)
                except ValueError:day=datetime.strptime(raw,'%d %B %Y').date()
            e.update(normalizedValue=day.isoformat(),status='resolved',vocabularySource='explicit/relative date parser')
        except ValueError:pass
    elif kind=='AGE':
        e.update(normalizedValue=str(int(value)),status='resolved',vocabularySource='provisional AGE extractor; absent from slot_schema.csv')
    elif kind=='ROAD_TYPE':
        e.update(normalizedValue=raw.casefold(),status='resolved',vocabularySource='road-type phrase rules')
    elif kind in {'INSURANCE_STATUS','CHALLAN_STATUS','LICENCE_STATUS','RC_STATUS','PUC_STATUS','FITNESS_STATUS','PERMIT_STATUS'}:
        lower=raw.casefold()
        negative=bool(re.search(r"\b(?:no|without|not|invalid|didn't|don't)\b|नहीं",lower))
        if 'unknown' in lower:
            e.update(normalizedValue='unknown',status='unresolved',vocabularySource='annotation status vocabulary')
        else:
            terms=('under dispute','referred to court','disqualified','suspended','seized','cancelled','transferred',
                   'unpaid','paid','issued','expired','lapsed','active','valid')
            identified=next((term for term in terms if re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',lower)),None)
            if kind=='CHALLAN_STATUS' and re.search(r'\b(?:received|got)\b|कटा|मिला|\bkat gaya\b',lower):identified='issued'
            e.update(normalizedValue='absent' if negative else identified,
                     status='resolved' if negative or identified else 'unresolved',
                     vocabularySource='annotation status vocabulary and negation rules')
    elif e.get('method') in {'explicit_schema_label','explicit_role'}:
        rows=[r for group in ontology()['slots'].values() for r in group if r['slot_name']==kind]
        allowed={v.casefold().replace('_',' '):v.casefold() for r in rows for v in r['allowed_values'].split('|')}
        key=value.casefold().replace('_',' ')
        if kind=='USER_ROLE' and key.startswith('vehicle '):key=key.removeprefix('vehicle ')
        if key in allowed and key not in {'unknown','uncertain'}:
            e.update(normalizedValue=allowed[key],status='resolved',vocabularySource='slot_schema.csv explicit value')
        elif any(r['data_type']=='string' for r in rows):
            e.update(normalizedValue=value,status='resolved',vocabularySource='explicit labelled text; not inferred')
    return e
