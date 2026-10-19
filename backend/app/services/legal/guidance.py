"""Deterministic guidance from confirmed facts and admissible dataset records."""
from datetime import datetime, timezone
from app.services.legal.knowledge import load_knowledge, refs
from app.services.legal.policy import provision_policy, source_policy, time_status, jurisdiction_status
from app.services.legal.index import retrieve
from app.services.legal.rules import evaluate, context, candidates


def procedure_policy(row, knowledge, event_date=None, jurisdiction=None):
    reasons=[]
    if row.get('review_status')!='VERIFIED':reasons.append('PROCEDURE_NOT_VERIFIED')
    reasons+=source_policy(knowledge['tables']['sources'].get(row.get('source_id')),knowledge,event_date,jurisdiction)['reasons']
    basis=refs(row.get('legal_basis_provision_ids'))
    if not basis:reasons.append('LEGAL_BASIS_MISSING')
    for provision_id in basis:
        check=provision_policy(knowledge['tables']['provisions'].get(provision_id),knowledge,event_date,jurisdiction)
        if check['status']!='eligible':reasons.append('LEGAL_BASIS_NOT_ELIGIBLE')
    service=row.get('official_service_id')
    if service and service not in knowledge['tables']['services']:reasons.append('SERVICE_REFERENCE_UNRESOLVED')
    steps=[s for s in knowledge['tables']['steps'].values() if s.get('procedure_id')==row['procedure_id']]
    if not steps:reasons.append('PROCEDURE_STEPS_MISSING')
    for step in steps:
        if source_policy(knowledge['tables']['sources'].get(step.get('source_id')),knowledge,event_date,jurisdiction)['status']!='eligible':
            reasons.append('STEP_SOURCE_NOT_ELIGIBLE')
        if any(ref not in knowledge['tables']['documents'] for ref in refs(step.get('required_document_ids'))):
            reasons.append('STEP_DOCUMENT_REFERENCE_UNRESOLVED')
    for field,table in [('required_document_ids','documents'),('required_form_ids','forms')]:
        if any(ref not in knowledge['tables'][table] for ref in refs(row.get(field))):
            reasons.append('REQUIRED_REFERENCE_UNRESOLVED')
        for ref in refs(row.get(field)):
            related=knowledge['tables'][table].get(ref)
            if related and related.get('review_status')!='VERIFIED':reasons.append('REQUIRED_RECORD_NOT_VERIFIED')
    if event_date:reasons+=time_status(row,event_date)
    if jurisdiction:reasons+=jurisdiction_status(row.get('jurisdiction_id'),jurisdiction,knowledge)
    return {'status':'eligible' if not reasons else 'excluded','reasons':sorted(set(reasons))}


def procedure_evidence(row, knowledge):
    """Resolve only existing IDs; keep ordered steps and record provenance."""
    tables=knowledge['tables']
    steps=sorted((s for s in tables['steps'].values() if s.get('procedure_id')==row['procedure_id']),
                 key=lambda s:(int(s.get('step_number') or 999),s['procedure_step_id']))
    return {'procedureId':row['procedure_id'],'evidenceId':f"EVID:{row['procedure_id']}",
            'sourceId':row['source_id'],'provisionIds':refs(row.get('legal_basis_provision_ids')),
            'serviceId':row.get('official_service_id') or None,
            'documentIds':refs(row.get('required_document_ids')),
            'formIds':refs(row.get('required_form_ids')),
            'steps':[{'stepId':s['procedure_step_id'],'title':s['step_title'],
                      'description':s['step_description'],'sourceId':s['source_id'],
                      'documentIds':refs(s.get('required_document_ids'))} for s in steps],
            'file':row['_file'],'row':row['_row']}


def readiness():
    knowledge=load_knowledge();tables=knowledge['tables'];summary={}
    for table,checker in [('sources',lambda r:source_policy(r,knowledge)),
                          ('provisions',lambda r:provision_policy(r,knowledge)),
                          ('procedures',lambda r:procedure_policy(r,knowledge))]:
        rows=tables[table].values()
        eligible=[r for r in rows if checker(r)['status']=='eligible']
        summary[table]={'total':len(tables[table]),'eligible':len(eligible),
                        'eligibleIds':[r[{'sources':'source_id','provisions':'provision_id','procedures':'procedure_id'}[table]] for r in eligible]}
    summary['rules']={'total':len(tables['rules']),'datasetReviewed':sum(r.get('review_status')=='VERIFIED' for r in tables['rules'].values())}
    usable_offences=[]
    for row in tables['offences'].values():
        source=source_policy(tables['sources'].get(row.get('source_id')),knowledge)
        provision=provision_policy(tables['provisions'].get(row.get('provision_id')),knowledge)
        if row.get('review_status')=='VERIFIED' and source['status']=='eligible' and provision['status']=='eligible':
            usable_offences.append(row['offence_id'])
    summary['offences']={'total':len(tables['offences']),'usablePenaltyRecords':len(usable_offences),
                         'usableIds':usable_offences}
    summary['speedLimits']={'total':len(tables['speed_limits']),
                            'reviewedNumericLimits':sum(r.get('review_status')=='VERIFIED' for r in tables['speed_limits'].values())}
    summary['malformedRecords']=knowledge['excluded']
    summary['sourceFingerprint']=knowledge['fingerprint']
    return summary


def assemble_evidence(matter):
    """Return facts, ranked evidence, rule decisions and unresolved links for future explainers."""
    knowledge=load_knowledge();facts,jurisdiction,event_date=context(matter)
    intent=matter.get('nlpAnalysis',{}).get('intent',{}).get('name') or matter['intent']['label']
    query=' '.join([intent]+[str(f.get('normalizedValue') or f['value']) for f in facts.values()])
    domains={r['domain'] for r in candidates(matter,knowledge)}
    search=retrieve(query,event_date,jurisdiction,domains=domains)
    rule_results=evaluate(matter)
    procedures=[];excluded_procedures=[]
    domains={knowledge['tables']['rules'][r['ruleId']]['domain'] for r in rule_results}
    for row in knowledge['tables']['procedures'].values():
        if row.get('domain') not in domains:continue
        check=procedure_policy(row,knowledge,event_date,jurisdiction)
        if check['status']=='eligible':procedures.append(row)
        else:excluded_procedures.append({'procedureId':row['procedure_id'],'reasons':check['reasons']})
    return {'knowledge':knowledge,'facts':facts,'jurisdiction':jurisdiction,'eventDate':event_date,
            'search':search,'rules':rule_results,'procedures':procedures,
            'procedureEvidence':[procedure_evidence(row,knowledge) for row in procedures],
            'excludedProcedures':excluded_procedures}


def generate(matter):
    assembled=assemble_evidence(matter)
    knowledge=assembled['knowledge'];facts=assembled['facts'];jurisdiction=assembled['jurisdiction']
    event_date=assembled['eventDate'];search=assembled['search'];rule_results=assembled['rules']
    matched=[r for r in rule_results if r['status']=='MATCHED']
    by_provision={r['provisionId']:r for r in matched}
    sources=[];mappings=[]
    for doc in search['results']:
        provision=knowledge['tables']['provisions'][doc['recordId']]
        source=knowledge['tables']['sources'][doc['sourceId']]
        source_type={'ACT':'Act','RULE':'Rules','NOTIFICATION':'Notification'}.get(source.get('instrument_type'),'Guidance')
        sources.append({'id':doc['recordId'],'title':doc['title'],'authority':doc['authority'],
                        'provision':provision['section_rule_number'],'relevantPoint':doc['passage'],
                        'sourceType':source_type,'sourceUrl':doc['sourceUrl'],'evidenceId':doc['evidenceId'],
                        'reviewStatus':doc['reviewStatus'],'admissibility':'eligible'})
        rule=by_provision.get(doc['recordId'])
        if rule:
            for fact_id in rule['matchedFactIds']:
                fact=next((f for f in facts.values() if f['id']==fact_id),None)
                if fact:
                    mappings.append({'id':f"{rule['ruleId']}:{fact_id}",'fact':f"{fact['label']}: {fact['value']}",
                                     'sourceId':doc['recordId'],'sourceTitle':doc['title'],
                                     'explanation':f"Dataset rule {rule['ruleId']} matched this confirmed fact. The provision appears relevant; this is not an offence finding.",
                                     'evidenceId':doc['evidenceId']})
    uncertainties=[]
    if not jurisdiction:uncertainties.append('The jurisdiction is unresolved, so source applicability cannot be established.')
    if not event_date:uncertainties.append('The event date is unresolved, so the relevant law version cannot be established.')
    if not sources:uncertainties.append('No eligible legal provision was retrieved for the confirmed context.')
    if not matched:uncertainties.append('No structured rule was established as applicable to the confirmed facts.')
    if any(r['status']=='INSUFFICIENT_CONTEXT' for r in rule_results):
        uncertainties.append('Some candidate rules need more confirmed facts or reviewed lookup data.')
    if any(r['status']=='UNSUPPORTED_CONDITION' for r in rule_results):
        uncertainties.append('Some dataset rule conditions or exceptions cannot yet be evaluated safely.')
    if any('SPEED_LIMIT_REVIEW_MISSING' in r['reasons'] for r in rule_results):
        uncertainties.append('Numeric speed-limit records lack legal-source review; no speed threshold or penalty is asserted.')
    procedures=assembled['procedures'];excluded_procedures=assembled['excludedProcedures']
    next_steps=[]
    for row in procedures[:4]:
        next_steps.append({'id':row['procedure_id'],'tag':'Check','title':row['procedure_name'],
                           'description':row['expected_outcome'] or row['eligibility'],
                           'evidenceId':f"EVID:{row['procedure_id']}"})
    if excluded_procedures and not next_steps:
        uncertainties.append('Related procedure records have unresolved source, legal-basis, or service references; procedural instructions are withheld.')
    if matter.get('language') in {'hindi','hinglish'}:
        uncertainties.append('Dataset multilingual explanations have not completed legal and language review; this guidance is supplied in English.')
    if sources:
        direct=f"The dataset identifies {sources[0]['title']} as potentially relevant to your confirmed situation. {sources[0]['relevantPoint']}"
    else:
        direct='The confirmed information is not enough to provide source-grounded legal guidance for this situation.'
    qualification=('This is legal information, not an offence finding. Source and provision review statuses come from the local dataset; '
                   'the application has not independently authenticated the linked government pages. '
                   'No numeric penalty, deadline, or procedural requirement is stated without an eligible supporting record.')
    return {'generatedAt':datetime.now(timezone.utc).isoformat(),'directAnswer':direct,
            'qualification':qualification,'sources':sources,'mappings':mappings,
            'uncertainties':list(dict.fromkeys(uncertainties)),'nextSteps':next_steps,
            'suggestedQuestions':[],
            'metadata':{'indexVersion':search['indexVersion'],'sourceFingerprint':search['sourceFingerprint'],
                        'retrievalMode':search['retrievalMode'],'eventDate':event_date,
                        'jurisdictionId':jurisdiction,'ruleEvaluations':rule_results,
                        'retrievedEvidence':[{'evidenceId':d['evidenceId'],'documentId':d['documentId'],
                                              'rank':d['rank'],'lexicalScore':d['lexicalScore'],
                                              'semanticScore':d['semanticScore']} for d in search['results']],
                        'evidenceIds':[s['evidenceId'] for s in sources]+[s['evidenceId'] for s in next_steps],
                        'generationMethod':'DETERMINISTIC_TEMPLATE_V1',
                        'retrievalExclusions':search['excluded'],
                        'procedureExclusions':excluded_procedures,
                        'procedureEvidence':assembled['procedureEvidence'],
                        'penaltyPolicy':'WITHHELD_UNVERIFIED_RELATIONSHIPS'}}
