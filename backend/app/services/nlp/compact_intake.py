"""Small wire contract for local inference; normalization stays server-side."""
import json
import re
from pydantic import BaseModel, ConfigDict, Field


class CompactMention(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    slot: str
    quote: str = Field(min_length=1, max_length=2000)


class CompactExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    facts: list[CompactMention] = Field(max_length=40)


WIRE_NAMES={'OBSERVED_SPEED':'speed','OBSERVED_SPEED_UNIT':'speed_unit','VEHICLE_CLASS':'vehicle','EVENT_DATE':'date'}

def wire_name(slot):return WIRE_NAMES.get(slot,slot.lower())

def wire_schema(slots, text, target):
    # Only two fields per fact; no repeated value, boolean or certainty boilerplate.
    item={'type':'array','items':{'type':'string','minLength':1,'maxLength':2000},'maxItems':8}
    return {'type':'object','properties':{'facts':{'type':'object','properties':{wire_name(slot):item for slot in sorted(slots)},
        'additionalProperties':False,'required':['speed','state','date','road_type','vehicle'],'maxProperties':12 if len(text)<=200 else 40}},'required':['facts'],'additionalProperties':False}


def expand_response(raw):
    data=json.loads(raw)
    if isinstance(data,dict) and isinstance(data.get('facts'),dict):
        mapped=[]
        for slot,quotes in data['facts'].items():
            if not isinstance(quotes,list):raise ValueError('OUTPUT_SCHEMA_INVALID')
            canonical=next((k for k,v in WIRE_NAMES.items() if v==slot),slot.upper())
            mapped.extend({'slot':canonical,'quote':quote} for quote in quotes)
        data={**data,'facts':mapped}
    if not isinstance(data,dict) or not isinstance(data.get('facts'),list):
        raise ValueError('OUTPUT_SCHEMA_INVALID')
    # Preserve strict validation of old wire responses/tests during migration.
    if any(isinstance(f,dict) and 'value' in f for f in data['facts']):
        return data
    compact=CompactExtraction.model_validate(data)
    facts=[]
    for mention in compact.facts:
        values=[mention.quote]
        if mention.slot=='OBSERVED_SPEED':
            values=re.findall(r'(?<!\w)\d{1,3}(?!\d)',mention.quote) or values
        for value in values:
            facts.append({'slot':mention.slot,'quote':mention.quote,'value':value,
                          'certainty':'ambiguous' if len(values)>1 else 'clear', 'approximate':False})
    return {'facts':facts}
