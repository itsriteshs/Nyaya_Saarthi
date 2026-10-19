# Phase 1 dataset findings

This report reflects the read-only audit of the checked-out files. Legal review labels are dataset metadata, not independent legal verification.

## Coverage

- Expected/scanned files: 23/23
- Records seen: 20214; parsed rows: 20213
- Critical errors: 8; warnings: 315

| File | Records seen | Parsed rows | Columns |
|---|---:|---:|---:|
| accident_relief_and_claims.csv | 30 | 30 | 23 |
| adaptive_conversations.jsonl | 3000 | 3000 | 18 |
| annotated_utterances.csv | 10000 | 10000 | 20 |
| case_law_interpretations.csv | 25 | 25 | 12 |
| coverage_registry.csv | 30 | 30 | 9 |
| document_requirements.csv | 30 | 30 | 21 |
| gold_evaluation_cases.csv | 420 | 420 | 22 |
| intents.csv | 58 | 58 | 12 |
| jurisdictions.csv | 37 | 37 | 9 |
| legal_provisions.csv | 11 | 11 | 12 |
| legal_sources.csv | 18 | 18 | 13 |
| offences_penalties.csv | 30 | 30 | 20 |
| official_forms.csv | 30 | 30 | 16 |
| official_services.csv | 30 | 30 | 13 |
| plain_language_multilingual.csv | 11 | 11 | 15 |
| procedure_steps.csv | 30 | 30 | 15 |
| procedures.csv | 30 | 29 | 22 |
| query_provision_relevance.csv | 4474 | 4474 | 11 |
| rule_logic.csv | 30 | 30 | 18 |
| safety_challenge_cases.csv | 1500 | 1500 | 12 |
| slot_schema.csv | 330 | 330 | 16 |
| speed_limits.csv | 30 | 30 | 15 |
| vehicle_classes.csv | 30 | 30 | 13 |

## Language labels

Counts across five labeled files; the same scenario may appear in several files. Other files cannot be counted reliably from a language label.

- english: 7744
- hindi: 5829
- hinglish: 5821

## Review status

Rows classified from their own review fields only:

- verified: 87
- not_verified: 3167
- pending_review: 15985
- unknown: 974

## Data issues

- UNRESOLVED_PLACEHOLDER_REFERENCE: 143
- POTENTIAL_SPLIT_LEAKAGE: 100
- TRAILING_EMPTY_COLUMNS: 58
- MISSING_REFERENCE: 16
- INVALID_URL: 3
- MALFORMED_RECORD: 1
- REQUIRED_REFERENCE_EMPTY: 1
- ADDITIONAL_SPLIT_LEAKAGE: 1

The 8 critical errors consist of one malformed `procedures.csv` record (line 26 has 21 instead of 22 fields), one blank required source ID in `offences_penalties.csv` (line 31), and six `query_provision_relevance.csv` query IDs absent from `annotated_utterances.csv`. There are 143 placeholder references and 16 missing references in total; 10 missing references are optional associations and remain warnings. No duplicate primary IDs were found among parsed rows. `intents.csv` has 58 extra empty trailing columns; these are preserved in the audit as warnings while the 58 records remain usable. Three service URLs fail syntax checks.

The split check found over 100 identical normalized texts appearing under different split labels; the JSON report lists 100 examples and one aggregate remainder issue. These may involve different dataset roles, so inspect provenance before treating them as confirmed training leakage.

## Phase 2 recommendations

1. Repair malformed CSV structure and resolve confirmed missing IDs at the source after human review. Preserve IDs and evaluation ground truth until reviewed.
2. Review placeholder legal provisions, services, forms, and procedure links with official material; do not infer laws or penalties from incomplete rows.
3. Keep evaluation and safety challenge cases separate from any training corpus, and investigate shared scenario/text leakage across splits.
4. Validate entity offset convention with dataset authors before training an extractor.
5. Add a curated source freshness policy before using any legal row for user guidance.

Full row-level evidence is in `dataset_audit.json`.
