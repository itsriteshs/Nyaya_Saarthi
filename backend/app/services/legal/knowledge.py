"""Cached legal tables with physical-row provenance and reproducible fingerprints."""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
from app.config import DATASET_DIR
from app.services.dataset_loader import load_dataset

FILES = {
    'sources': ('legal_sources.csv', 'source_id'),
    'provisions': ('legal_provisions.csv', 'provision_id'),
    'rules': ('rule_logic.csv', 'rule_id'),
    'offences': ('offences_penalties.csv', 'offence_id'),
    'speed_limits': ('speed_limits.csv', 'speed_rule_id'),
    'procedures': ('procedures.csv', 'procedure_id'),
    'steps': ('procedure_steps.csv', 'procedure_step_id'),
    'documents': ('document_requirements.csv', 'requirement_id'),
    'forms': ('official_forms.csv', 'form_id'),
    'services': ('official_services.csv', 'service_id'),
    'accident_relief': ('accident_relief_and_claims.csv', 'relief_rule_id'),
    'case_law': ('case_law_interpretations.csv', 'case_id'),
    'explanations': ('plain_language_multilingual.csv', 'explanation_id'),
    'coverage': ('coverage_registry.csv', 'coverage_id'),
    'jurisdictions': ('jurisdictions.csv', 'jurisdiction_id'),
    'vehicles': ('vehicle_classes.csv', 'vehicle_class_id'),
    'intents': ('intents.csv', 'intent_id'),
}

def refs(value):
    """Resolve a documented ID list, preserving placeholder strings for diagnostics."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    raw = str(value).strip()
    if raw.startswith('['):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return refs(parsed)
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in raw.replace(';', '|').split('|') if part.strip()]

def parse_json(value):
    if not value:
        return {}, None
    try:
        parsed = json.loads(value)
        return (parsed, None) if isinstance(parsed, dict) else ({}, 'JSON_NOT_OBJECT')
    except (TypeError, json.JSONDecodeError):
        return {}, 'INVALID_JSON'

def fingerprint():
    digest = sha256()
    for name, _ in FILES.values():
        path = DATASET_DIR / name
        digest.update(name.encode())
        digest.update(sha256(path.read_bytes()).digest())
    return digest.hexdigest()

@lru_cache(maxsize=1)
def load_knowledge():
    tables = {}
    excluded = []
    for table, (filename, id_field) in FILES.items():
        headers, rows = load_dataset(DATASET_DIR / filename)
        if id_field not in headers:
            raise ValueError(f'{filename}: missing {id_field}')
        indexed = {}
        for line, row in rows:
            if not isinstance(row, dict) or '__column_error__' in row or '__parse_error__' in row:
                excluded.append({'table': table, 'file': filename, 'row': line, 'reason': 'MALFORMED_RECORD'})
                continue
            record_id = row.get(id_field, '')
            if not record_id or record_id in indexed:
                excluded.append({'table': table, 'file': filename, 'row': line, 'reason': 'MISSING_OR_DUPLICATE_ID'})
                continue
            indexed[record_id] = {**row, '_file': filename, '_row': line}
        tables[table] = indexed
    return {'tables': tables, 'excluded': excluded, 'fingerprint': fingerprint()}
