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
    assert report['review_dimensions']
    assert report['split_analysis']['cross_split_texts'] >= 0
    assert any(i['code'] == 'UNRESOLVED_PLACEHOLDER_REFERENCE' for i in report['issues'])

def test_missing_placeholder_and_duplicate_ids(tmp_path):
    (tmp_path / 'legal_sources.csv').write_text('source_id\nSRC_OK\nSRC_OK\n', encoding='utf-8')
    (tmp_path / 'legal_provisions.csv').write_text('provision_id,source_id,jurisdiction_id\nP1,SRC_OK,\nP2,SRC_MISSING,\nP3,SRC_PENDING_ADD,\n', encoding='utf-8')
    report = audit_dataset(tmp_path)
    codes = {item['code'] for item in report['issues']}
    assert {'DUPLICATE_PRIMARY_ID', 'MISSING_REFERENCE', 'UNRESOLVED_PLACEHOLDER_REFERENCE'} <= codes
    assert report['summary']['critical_errors'] > 0

def test_synthetic_query_and_form_namespace(tmp_path):
    (tmp_path / 'annotated_utterances.csv').write_text('utterance_id,text\nU1,Example\n')
    (tmp_path / 'query_provision_relevance.csv').write_text(
        'pair_id,query_id,query_text\nP1,Q_SYN_X_1,Standalone query\nP2,U1,Example\n')
    (tmp_path / 'official_forms.csv').write_text('form_id\nFORM_2\n')
    (tmp_path / 'document_requirements.csv').write_text('requirement_id\nREQ_1\n')
    (tmp_path / 'procedure_steps.csv').write_text('procedure_step_id,required_document_ids\nS1,FORM_2|REQ_1\n')
    report = audit_dataset(tmp_path)
    assert any(i['code'] == 'STANDALONE_QUERY_ID' and i['value'] == 'Q_SYN_X_1' for i in report['issues'])
    assert any(i['code'] == 'REFERENCE_TYPE_MISMATCH' and i['value'] == 'FORM_2' for i in report['issues'])
    assert not any(i['code'] == 'MISSING_REFERENCE' and i['value'] in {'Q_SYN_X_1','FORM_2'} for i in report['issues'])

def test_review_dimensions_and_malformed_record_value(tmp_path):
    from app.services.dataset_validator import review_label
    assert review_label({'review_status': 'UNDER_REVIEW'}) == 'pending_review'
    assert review_label({'legal_reviewer': 'PENDING'}) == 'pending_review'
    assert review_label({'human_review_status': 'pending', 'legal_review_status': 'not_reviewed'}) == 'not_verified'
    (tmp_path / 'procedures.csv').write_text('procedure_id,source_id,review_status\nP1,SRC_1\n', encoding='utf-8')
    report = audit_dataset(tmp_path)
    malformed = next(i for i in report['issues'] if i['code'] == 'MALFORMED_RECORD')
    assert malformed['value']['actual_columns'] == 2
    assert malformed['value']['expected_columns'] == 3
