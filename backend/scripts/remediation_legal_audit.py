"""Per-record fail-closed coverage audit; never changes legal review flags."""
import json
from app.config import BACKEND_DIR
from app.services.legal.knowledge import load_knowledge, refs
from app.services.legal.policy import provision_policy, source_policy
from app.services.legal.guidance import readiness, procedure_policy


def run(label):
    knowledge=load_knowledge(); tables=knowledge['tables']; records=[]
    for table, key in [('provisions','provision_id'), ('procedures','procedure_id'),
                       ('offences','offence_id'), ('speed_limits','speed_rule_id')]:
        for row in tables[table].values():
            if table=='provisions': result=provision_policy(row,knowledge)
            elif table=='procedures': result=procedure_policy(row,knowledge)
            else:
                reasons=list(source_policy(tables['sources'].get(row.get('source_id')),knowledge)['reasons'])
                if row.get('review_status')!='VERIFIED': reasons.append('RECORD_LEGAL_REVIEW_PENDING')
                if table=='offences':
                    reasons+=provision_policy(tables['provisions'].get(row.get('provision_id')),knowledge)['reasons']
                result={'status':'eligible' if not reasons else 'excluded','reasons':sorted(set(reasons))}
            groups=[]
            if any('REFERENCE' in r or 'URL' in r or 'MISSING' in r for r in result['reasons']): groups.append('authoritative_reference_lookup')
            if any('VERIFIED' in r or 'REVIEW' in r or 'COMMENCEMENT' in r for r in result['reasons']): groups.append('qualified_legal_review')
            if row.get('active_status')=='PENDING_COMMENCEMENT': groups.append('remain_excluded_pending_commencement')
            records.append({'table':table,'id':row[key],'sourceId':row.get('source_id'),'file':row['_file'],
                            'row':row['_row'],**result,'resolutionCategories':groups})
    output=BACKEND_DIR/'experiments/metrics'/f'remediation_legal_{label}.json'
    if output.exists(): raise FileExistsError(output)
    result={'coverage':readiness(),'records':records,'independentLegalReview':False}
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result['coverage'],indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True)
    run(parser.parse_args().label)
