"""Intent-specific required slots; unsupported conditions stay unresolved."""
import json
from app.services.nlp.ontology import ontology

PROVISIONAL_AGE={'intent_id':'INT016','slot_name':'AGE','status':'provisional',
                 'source':'INT016.conditional_slot_ids and 26 annotated utterances; absent from slot_schema.csv'}

def detect_slots(intent_id: str, entities: list[dict], *, required_slots=(), configured_rows=None):
    configured=ontology()['slots'].get(intent_id,[]) if configured_rows is None else configured_rows
    by_type={}
    for entity in entities:by_type.setdefault(entity['type'],[]).append(entity)
    missing=[];unresolved=[];found=0;total=0
    for row in sorted(configured,key=lambda r:int(r['ask_priority'] or 999)):
        slot=row['slot_name'];level=row['required_level']
        try:condition=json.loads(row['required_when_json'] or '{}').get('when')
        except (ValueError,TypeError):condition='invalid_json'
        values=by_type.get(slot,[])
        valid=[x for x in values if x['status']=='resolved']
        conflicting=len({str(x['normalizedValue']) for x in valid})>1
        ambiguous=bool(values) and (not valid or conflicting)
        if level=='required' and condition=='intent_context' or slot in required_slots:
            total+=1
            if valid and not conflicting:found+=1
            else:
                item={'slot':slot,'label':row['slot_display_name'],'priority':int(row['ask_priority'] or 999),
                      'question':row['question_template_en'],'reason':'ambiguous_or_conflicting' if ambiguous else 'missing'}
                missing.append(item)
        elif level=='conditional':
            if not valid or conflicting:
                unresolved.append({'slot':slot,'reason':'condition_not_implemented',
                                   'condition':condition,'present':bool(valid) and not conflicting})
        elif level=='optional':
            continue
        else:
            unresolved.append({'slot':slot,'reason':'unsupported_requirement','condition':condition})
    if intent_id=='INT016':
        unresolved.append({'slot':'AGE','reason':'provisional_schema_gap',
                           'condition':'only_when_relevant_to_rule_or_situation','present':bool(by_type.get('AGE'))})
    missing.sort(key=lambda x:x['priority'])
    percentage=round(found/total*100) if total else 0
    if unresolved and percentage==100:percentage=99
    status='needs_context' if missing else 'conditional_unresolved' if unresolved else 'ready_for_review' if total else 'no_configured_required_slots'
    return {'missingSlots':missing,'unresolvedSlots':unresolved,
            'readiness':{'found':found,'total':total,'percentage':percentage,'status':status}}
