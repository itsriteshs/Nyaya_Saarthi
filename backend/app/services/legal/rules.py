"""Evaluate reviewed structured rules without treating missing predicates as true."""
from app.services.legal.knowledge import load_knowledge, parse_json, refs
from app.services.legal.policy import provision_policy, time_status, jurisdiction_status

DOMAIN_HINTS = {
    'SPEEDING': {'SPEED'}, 'INSURANCE': {'INSURANCE'}, 'REGISTRATION': {'REGISTRATION'},
    'LICENCE': {'LICENSING'}, 'HELMET': {'HELMET'}, 'SEATBELT': {'SEATBELT'},
    'CHALLAN': {'ENFORCEMENT'}, 'ACCIDENT': {'ACCIDENTS','HIT_AND_RUN','COMPENSATION'},
    'HIT_AND_RUN': {'HIT_AND_RUN','ACCIDENTS'},
}

def matter_facts(matter):
    return {f['key']:f for f in matter['facts'] if f.get('confirmed') and f.get('provenance')=='USER_CONFIRMED'
            and f.get('resolutionStatus','resolved')=='resolved'}

def context(matter):
    facts=matter_facts(matter)
    state=facts.get('STATE',{}).get('normalizedId')
    date=facts.get('EVENT_DATE',{}).get('normalizedValue') or facts.get('CHALLAN_DATE',{}).get('normalizedValue')
    return facts,state,date

def candidates(matter, knowledge):
    name=matter.get('nlpAnalysis',{}).get('intent',{}).get('name','')
    domains=set()
    for term, group in DOMAIN_HINTS.items():
        if term in name:domains|=group
    if not domains:
        broad=matter.get('nlpAnalysis',{}).get('intent',{}).get('domain','').upper()
        domains=DOMAIN_HINTS.get(broad,set())
    return sorted((r for r in knowledge['tables']['rules'].values() if r['domain'] in domains),
                  key=lambda r:(int(r['priority'] or 999),r['rule_id']))

def _condition(key, expected, facts):
    names={'insurance_status_not_valid':'INSURANCE_STATUS','rc_status_not_valid':'RC_STATUS',
           'puc_status_not_valid':'PUC_STATUS','licence_status_not_valid':'LICENCE_STATUS',
           'death_present':'DEATH_PRESENT','injury_present':'INJURY_PRESENT',
           'other_vehicle_identified':'OTHER_VEHICLE_IDENTIFIED',
           'police_reported_promptly':'POLICE_REPORTED'}
    if key=='observed_speed_gt' and str(expected).startswith('lookup:'):
        return 'unknown',None,'SPEED_LIMIT_REVIEW_MISSING'
    if key in names:
        fact=facts.get(names[key])
        if not fact:return 'unknown',None,'REQUIRED_FACT_MISSING'
        value=str(fact.get('normalizedValue') or fact['value']).casefold()
        if key.endswith('_not_valid'):
            truth=value not in {'valid','active','present'}
        else:truth=value in {'yes','true','1'}
        return ('true' if truth==expected else 'false'),fact['id'],None
    if key in {'age_gt','age_lte'}:
        fact=facts.get('AGE')
        if not fact:return 'unknown',None,'REQUIRED_FACT_MISSING'
        try:
            age=int(fact.get('normalizedValue') or fact['value'])
            truth=age>int(expected) if key=='age_gt' else age<=int(expected)
            return ('true' if truth else 'false'),fact['id'],None
        except (ValueError,TypeError):return 'unknown',None,'INVALID_NUMERIC_FACT'
    if key=='vehicle_class_in' and isinstance(expected,list):
        fact=facts.get('VEHICLE_CLASS')
        if not fact:return 'unknown',None,'REQUIRED_FACT_MISSING'
        if not fact.get('normalizedId'):return 'unknown',fact['id'],'VEHICLE_CATEGORY_UNRESOLVED'
        return ('true' if fact['normalizedId'] in expected else 'false'),fact['id'],None
    if key=='state':
        fact=facts.get('STATE')
        if not fact:return 'unknown',None,'REQUIRED_FACT_MISSING'
        return ('true' if fact.get('normalizedValue')==expected else 'false'),fact['id'],None
    if key in {'wearing_helmet','wearing_seatbelt'}:
        fact=facts.get(key.upper())
        if not fact:return 'unknown',None,'REQUIRED_FACT_MISSING'
        value=str(fact.get('normalizedValue') or fact['value']).casefold() in {'yes','true','1'}
        return ('true' if value==expected else 'false'),fact['id'],None
    return 'unsupported',None,'UNSUPPORTED_CONDITION'

def evaluate_rule(rule, matter, knowledge):
    facts,jurisdiction,event_date=context(matter)
    provision=knowledge['tables']['provisions'].get(rule['provision_id'])
    reasons=[];matched=[];evaluated=[]
    if rule.get('review_status')!='VERIFIED':reasons.append('RULE_NOT_VERIFIED')
    base_provision_check=provision_policy(provision,knowledge)
    provision_check=provision_policy(provision,knowledge,event_date,jurisdiction)
    reasons+=provision_check['reasons']
    if not provision:reasons.append('PROVISION_REFERENCE_MISSING')
    if not jurisdiction:reasons.append('JURISDICTION_UNRESOLVED')
    if not event_date:reasons.append('DATE_APPLICABILITY_UNKNOWN')
    if event_date:reasons+=time_status(rule,event_date)
    if jurisdiction:reasons+=jurisdiction_status(rule.get('jurisdiction_id'),jurisdiction,knowledge)
    if rule.get('vehicle_class_id'):
        vehicle=facts.get('VEHICLE_CLASS')
        if not vehicle or not vehicle.get('normalizedId'):
            reasons.append('VEHICLE_CATEGORY_UNRESOLVED')
        elif vehicle['normalizedId']!=rule['vehicle_class_id']:
            # No dataset relationship proves that an informal motor-car class is an LMV.
            reasons.append('VEHICLE_CLASS_SCOPE_UNPROVEN')
    missing=[slot for slot in refs(rule.get('required_slot_ids')) if slot not in facts]
    if missing:reasons.append('REQUIRED_FACT_MISSING')
    condition,error=parse_json(rule.get('condition_json'))
    if error:reasons.append(error)
    for key,expected in condition.items():
        result,fact_id,reason=_condition(key,expected,facts)
        evaluated.append({'predicate':key,'expected':expected,'result':result,'factId':fact_id})
        if fact_id and result=='true':matched.append(fact_id)
        if reason:reasons.append(reason)
    exceptions,error=parse_json(rule.get('exception_json'))
    if error:reasons.append(error)
    if exceptions:
        # These fields are narrative references, not supported declarative predicates.
        reasons.append('EXCEPTION_NOT_EVALUATED')
    if rule.get('review_status')!='VERIFIED' or base_provision_check['status']!='eligible':
        status='EXCLUDED_UNVERIFIED'
    elif any(x in reasons for x in ('SOURCE_EXPIRED_FOR_EVENT','JURISDICTION_MISMATCH')):
        status='NOT_MATCHED'
    elif any(x in reasons for x in ('UNSUPPORTED_CONDITION','INVALID_JSON','JSON_NOT_OBJECT','EXCEPTION_NOT_EVALUATED')):
        status='UNSUPPORTED_CONDITION'
    elif missing or any(x in reasons for x in ('DATE_APPLICABILITY_UNKNOWN','INVALID_EFFECTIVE_DATE','JURISDICTION_UNRESOLVED',
          'SPEED_LIMIT_REVIEW_MISSING','VEHICLE_CATEGORY_UNRESOLVED','VEHICLE_CLASS_SCOPE_UNPROVEN')):
        status='INSUFFICIENT_CONTEXT'
    elif any(item['result']=='false' for item in evaluated):status='NOT_MATCHED'
    elif any(item['result'] in {'unknown','unsupported'} for item in evaluated):status='INSUFFICIENT_CONTEXT'
    else:status='MATCHED'
    return {'ruleId':rule['rule_id'],'status':status,'provisionId':rule['provision_id'],
            'sourceId':provision['source_id'] if provision else None,'matchedFactIds':sorted(set(matched)),
            'missingSlots':missing,'conditions':evaluated,'exception':exceptions,
            'conclusionType':rule.get('conclusion_type'),
            'conclusionData':parse_json(rule.get('conclusion_json'))[0],
            'reasons':sorted(set(reasons)),'reviewStatus':rule['review_status'],
            'file':rule['_file'],'row':rule['_row']}

def evaluate(matter):
    knowledge=load_knowledge()
    return [evaluate_rule(rule,matter,knowledge) for rule in candidates(matter,knowledge)]
