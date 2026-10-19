# Dataset audit

Run: 2026-10-19T10:00:09.018725+00:00

## Summary

- dataset_files: 23
- expected_files: 23
- records_seen: 20214
- total_rows: 20213
- critical_errors: 2
- warnings: 341
- info: 6
- issue_codes: {'TRAILING_EMPTY_COLUMNS': 58, 'INVALID_URL': 3, 'MALFORMED_RECORD': 1, 'UNRESOLVED_PLACEHOLDER_REFERENCE': 143, 'REQUIRED_REFERENCE_EMPTY': 1, 'REFERENCE_TYPE_MISMATCH': 8, 'MISSING_REFERENCE': 28, 'STANDALONE_QUERY_ID': 6, 'POTENTIAL_SPLIT_LEAKAGE': 100, 'ADDITIONAL_SPLIT_LEAKAGE': 1}

## Files

| Dataset | Records seen | Parsed rows | Columns | IDs |
|---|---:|---:|---:|---:|
| accident_relief_and_claims.csv | 30 | 30 | 23 | 30 |
| adaptive_conversations.jsonl | 3000 | 3000 | 18 | 3000 |
| annotated_utterances.csv | 10000 | 10000 | 20 | 10000 |
| case_law_interpretations.csv | 25 | 25 | 12 | 25 |
| coverage_registry.csv | 30 | 30 | 9 | 30 |
| document_requirements.csv | 30 | 30 | 21 | 30 |
| gold_evaluation_cases.csv | 420 | 420 | 22 | 420 |
| intents.csv | 58 | 58 | 12 | 58 |
| jurisdictions.csv | 37 | 37 | 9 | 37 |
| legal_provisions.csv | 11 | 11 | 12 | 11 |
| legal_sources.csv | 18 | 18 | 13 | 18 |
| offences_penalties.csv | 30 | 30 | 20 | 30 |
| official_forms.csv | 30 | 30 | 16 | 30 |
| official_services.csv | 30 | 30 | 13 | 30 |
| plain_language_multilingual.csv | 11 | 11 | 15 | 11 |
| procedure_steps.csv | 30 | 30 | 15 | 30 |
| procedures.csv | 30 | 29 | 22 | 29 |
| query_provision_relevance.csv | 4474 | 4474 | 11 | 4474 |
| rule_logic.csv | 30 | 30 | 18 | 30 |
| safety_challenge_cases.csv | 1500 | 1500 | 12 | 1500 |
| slot_schema.csv | 330 | 330 | 16 | 330 |
| speed_limits.csv | 30 | 30 | 15 | 30 |
| vehicle_classes.csv | 30 | 30 | 13 | 30 |

## Issue counts

- UNRESOLVED_PLACEHOLDER_REFERENCE: 143
- POTENTIAL_SPLIT_LEAKAGE: 100
- TRAILING_EMPTY_COLUMNS: 58
- MISSING_REFERENCE: 28
- REFERENCE_TYPE_MISMATCH: 8
- STANDALONE_QUERY_ID: 6
- INVALID_URL: 3
- MALFORMED_RECORD: 1
- REQUIRED_REFERENCE_EMPTY: 1
- ADDITIONAL_SPLIT_LEAKAGE: 1

Full row-level findings are in `dataset_audit.json`.
