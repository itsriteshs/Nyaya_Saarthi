"""Frozen-evidence development retest and exhaustive archived-output audit.

Outputs never overwrite Phase 6 runs. Runtime-unavailable cells are not generations.
"""
import argparse
import hashlib
import json
from collections import Counter
from app.config import BACKEND_DIR
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.model_registry import MODELS, settings
from app.services.llm.prompt_builder import messages, PROMPT_VERSION, response_schema
from app.services.llm.response_parser import parse_response
from app.services.llm.grounding_validator import validate, OUTCOME
from app.services.llm.output_checks import check_language

ROOT=BACKEND_DIR/'experiments'


def assess(text, package, language):
    output=parse_response(text)
    verdict=validate(output,package)
    reasons=verdict['reasonCodes'][:]
    try: check_language(output,language)
    except ValueError as exc: reasons.append(str(exc))
    return {'accepted':not reasons,'reasonCodes':sorted(set(reasons)), 'validation':verdict}


def run(replay=False, run_id=''):
    path=ROOT/'manifests/phase6_evidence_packages.json'
    frozen=json.loads(path.read_text(encoding='utf-8'))
    config=settings();provider=OllamaProvider(config['url']);availability=provider.availability()
    cases={r['caseId']:r for r in frozen['cases']};all_results={}
    for model,spec in MODELS.items():
        records=[]
        if replay:
            for line in (ROOT/f'predictions/phase6_llm_{model}.jsonl').read_text(encoding='utf-8').splitlines():
                old=json.loads(line); package=cases[old['caseId']]['package']
                result=assess(old['rawOutput'],package,old['language'])
                outcome=[m.group() for m in OUTCOME.finditer(' '.join([old['parsedOutput']['answer'],old['parsedOutput']['explanation']]+old['parsedOutput']['uncertainties']))]
                records.append({'caseId':old['caseId'],'language':old['language'],'originalStatus':old['status'],
                                'originalReasonCodes':old['validation']['reasonCodes'], 'currentReplay':result,
                                'outcomeMatches':outcome,'rawOutput':old['rawOutput'],
                                'schemaFailure':False,'invalidEvidenceIDs':old['validation']['unsupportedCitations'],
                                'truncationObserved':False,'runtimeErrorObserved':False,
                                'semanticLegalSupport':'not independently verified; valid IDs do not establish support'})
        else:
            for case in frozen['cases']:
                for language in ('english','hindi','hinglish'):
                    row={'caseId':case['caseId'],'language':language,'evidenceFingerprint':case['package']['fingerprint'],
                         'modelId':model,'runtimeTag':spec.runtime_name,'promptVersion':PROMPT_VERSION,
                         'temperature':0,'maxTokens':config['maxTokens'],'seed':471,'contextTokens':8192,
                         'format':'Explanation JSON schema','generationAttempted':False,'fallbackUsed':True}
                    if not availability['models'][model]['available']:
                        row.update(status='blocked',reasonCodes=[availability['models'][model]['status'].upper()])
                    else:
                        try:
                            row['generationAttempted']=True
                            generation=provider.generate(spec.runtime_name,messages(case['package'],case['question'],language),
                                temperature=0,max_tokens=config['maxTokens'],timeout=config['timeout'],
                                output_schema=response_schema(case['package'],language))
                            row.update(rawOutput=generation.text,latencyMs=generation.duration_ms,
                                       outputTokens=generation.output_tokens,installedDigest=availability['models'][model].get('digest'))
                            row.update(assess(generation.text,case['package'],language))
                            row.update(status='accepted' if row['accepted'] else 'rejected',fallbackUsed=not row['accepted'])
                        except (ValueError,RuntimeFailure) as exc: row.update(status='rejected',reasonCodes=[str(exc)])
                    records.append(row)
        name=f'remediation_llm_{"archive_audit" if replay else "dev"}{run_id}_{model}'
        dest=ROOT/f'predictions/{name}.jsonl'
        if dest.exists(): raise FileExistsError(dest)
        dest.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
        generated=[r for r in records if r.get('rawOutput') and not replay]
        accepted=sum(r.get('accepted',False) for r in generated)
        all_results[model]={'cells':len(records),'generatedOutputs':len(generated),'accepted':accepted,
                            'acceptanceRate':accepted/len(generated) if generated else None,
                            'fallbackCells':sum(r.get('fallbackUsed',False) for r in records),
                            'reasons':dict(Counter(reason for r in records for reason in r.get('reasonCodes',[])))}
        if replay:
            all_results[model]['archivedOutputs']=len(records)
            all_results[model]['originalAccepted']=sum(r['originalStatus']=='accepted' for r in records)
            all_results[model]['replayAccepted']=sum(r['currentReplay']['accepted'] for r in records)
            all_results[model]['replayReasons']=dict(Counter(c for r in records for c in r['currentReplay']['reasonCodes']))
    result={'kind':'archived replay, not new inference' if replay else 'development retest, not held-out',
            'frozenEvidenceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'models':all_results,
            'runtime':availability,'semanticSupportIndependentlyReviewed':False}
    (ROOT/f'metrics/remediation_llm_{"archive_audit" if replay else "dev"}{run_id}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--replay',action='store_true');parser.add_argument('--run-id',default='')
    args=parser.parse_args();run(args.replay,args.run_id)
