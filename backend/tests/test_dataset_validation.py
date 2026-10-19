import json
from pathlib import Path
from app.config import DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.dataset_validator import audit_dataset, references

def test_loader_csv_jsonl_and_bom(tmp_path):
    csv = tmp_path / 'sample.csv'
    csv.write_text('\ufeffid,name\n1,A\n', encoding='utf-8')
    assert load_dataset(csv)[1][0][1]['id'] == '1'
    jsonl = tmp_path / 'sample.jsonl'
    jsonl.write_text('{"id":"1"}\nnot json\n', encoding='utf-8')
    assert len(load_dataset(jsonl)[1]) == 2
    assert '__parse_error__' in load_dataset(jsonl)[1][1][1]
    csv.write_text('', encoding='utf-8')
    assert load_dataset(csv) == ([], [])

def test_reference_formats():
    assert references('A|B;C') == ['A','B','C']
    assert references('["A", "B"]') == ['A','B']
    assert references('') == []

def test_complete_audit():
    report = audit_dataset(DATASET_DIR)
    assert report['summary']['dataset_files'] == 23
    assert report['summary']['total_rows'] > 0
    assert report['relationship_checks']
    assert any(i['code'] == 'UNRESOLVED_PLACEHOLDER_REFERENCE' for i in report['issues'])

def test_missing_placeholder_and_duplicate_ids(tmp_path):
    (tmp_path / 'legal_sources.csv').write_text('source_id\nSRC_OK\nSRC_OK\n', encoding='utf-8')
    (tmp_path / 'legal_provisions.csv').write_text('provision_id,source_id,jurisdiction_id\nP1,SRC_OK,\nP2,SRC_MISSING,\nP3,SRC_PENDING_ADD,\n', encoding='utf-8')
    report = audit_dataset(tmp_path)
    codes = {item['code'] for item in report['issues']}
    assert {'DUPLICATE_PRIMARY_ID', 'MISSING_REFERENCE', 'UNRESOLVED_PLACEHOLDER_REFERENCE'} <= codes
    assert report['summary']['critical_errors'] > 0
