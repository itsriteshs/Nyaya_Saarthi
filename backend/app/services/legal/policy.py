"""Conservative dataset-review and source-link admissibility policy."""
from datetime import date
from urllib.parse import urlparse

OFFICIAL_HOSTS = {'www.indiacode.nic.in', 'indiacode.nic.in', 'morth.gov.in',
                  'www.mha.gov.in', 'mha.gov.in', 'egazette.gov.in'}

def official_url(url):
    try:
        parsed = urlparse(url or '')
        return parsed.scheme == 'https' and parsed.hostname in OFFICIAL_HOSTS and bool(parsed.path)
    except ValueError:
        return False

def time_status(row, event_date):
    if not event_date:
        return ['DATE_APPLICABILITY_UNKNOWN']
    try:
        day = date.fromisoformat(event_date)
        start = date.fromisoformat(row['effective_from']) if row.get('effective_from') else None
        end = date.fromisoformat(row['effective_to']) if row.get('effective_to') else None
    except ValueError:
        return ['INVALID_EFFECTIVE_DATE']
    if start and day < start or end and day > end:
        return ['SOURCE_EXPIRED_FOR_EVENT']
    return []

def jurisdiction_status(row_jurisdiction, fact_jurisdiction, knowledge):
    if not fact_jurisdiction:
        return ['JURISDICTION_UNRESOLVED']
    if row_jurisdiction == fact_jurisdiction:
        return []
    central = 'JX_IN_CENTRAL'
    if row_jurisdiction == central and fact_jurisdiction in knowledge['tables']['jurisdictions']:
        return []
    return ['JURISDICTION_MISMATCH']

def source_policy(source, knowledge, event_date=None, jurisdiction_id=None):
    reasons=[]
    if not source:
        return {'status':'excluded','reasons':['SOURCE_REFERENCE_MISSING']}
    if not source.get('source_id'):reasons.append('SOURCE_ID_MISSING')
    if not source.get('source_title'):reasons.append('SOURCE_TITLE_MISSING')
    if not source.get('issuing_authority'):reasons.append('ISSUING_AUTHORITY_MISSING')
    if source.get('jurisdiction_id') not in knowledge['tables']['jurisdictions']:
        reasons.append('SOURCE_JURISDICTION_INVALID')
    if not official_url(source.get('official_url')):reasons.append('OFFICIAL_URL_UNAVAILABLE')
    if source.get('is_primary_source','').upper() != 'TRUE':reasons.append('NOT_PRIMARY_SOURCE')
    if source.get('review_status') != 'VERIFIED':reasons.append('SOURCE_NOT_VERIFIED')
    if source.get('commencement_status') != 'FULLY_COMMENCED':reasons.append('COMMENCEMENT_NOT_ESTABLISHED')
    if not source.get('last_verified_at'):reasons.append('SOURCE_REVIEW_DATE_MISSING')
    if event_date is not None:reasons += time_status(source,event_date)
    if jurisdiction_id is not None:reasons += jurisdiction_status(source.get('jurisdiction_id'),jurisdiction_id,knowledge)
    excluded={'SOURCE_REFERENCE_MISSING','SOURCE_JURISDICTION_INVALID','SOURCE_EXPIRED_FOR_EVENT',
              'JURISDICTION_MISMATCH','INVALID_EFFECTIVE_DATE'}
    status='excluded' if excluded.intersection(reasons) else 'conditional' if reasons else 'eligible'
    return {'status':status,'reasons':reasons}

def provision_policy(provision, knowledge, event_date=None, jurisdiction_id=None):
    if not provision:return {'status':'excluded','reasons':['PROVISION_REFERENCE_MISSING']}
    source=knowledge['tables']['sources'].get(provision.get('source_id'))
    result=source_policy(source,knowledge,event_date,jurisdiction_id)
    reasons=list(result['reasons'])
    if provision.get('review_status')!='VERIFIED':reasons.append('LEGAL_REVIEW_PENDING')
    if not provision.get('official_text'):reasons.append('OFFICIAL_TEXT_MISSING')
    if provision.get('active_status') not in {'ACTIVE',''}:reasons.append('PROVISION_NOT_ACTIVE')
    if provision.get('jurisdiction_id') not in knowledge['tables']['jurisdictions']:
        reasons.append('PROVISION_JURISDICTION_INVALID')
    if event_date is not None:reasons += time_status(provision,event_date)
    if jurisdiction_id is not None:reasons += jurisdiction_status(provision.get('jurisdiction_id'),jurisdiction_id,knowledge)
    excluded={'PROVISION_REFERENCE_MISSING','PROVISION_JURISDICTION_INVALID','PROVISION_NOT_ACTIVE',
              'SOURCE_EXPIRED_FOR_EVENT','JURISDICTION_MISMATCH','INVALID_EFFECTIVE_DATE'}
    status='excluded' if excluded.intersection(reasons) else 'conditional' if reasons else 'eligible'
    return {'status':status,'reasons':sorted(set(reasons))}
