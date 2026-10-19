# Phase 1 dataset findings

This report reflects the read-only audit of the checked-out files. Legal review labels are dataset metadata, not independent legal verification.

## Coverage

- Expected/scanned files: 23/23
- Records seen: 20214; parsed rows: 20213
- Critical errors after validator fixes: 2; warnings: 341; informational standalone query IDs: 6

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
- pending_review: 16414
- unknown: 545

## Data issues

The corrected audit reports 143 unresolved placeholder references, 28 missing references, 8 form/document namespace mismatches, 58 extra empty CSV fields, 3 non-URL service values, and 101 split-overlap warning entries. Its two errors are one malformed challan procedure row and one missing required source ID. The original eight-error audit included six synthetic query IDs incorrectly treated as annotation references.

See [Phase 1 verification](PHASE1_VERIFICATION.md) for all eight original errors, warning impact, review-status breakdown, and Phase 2 readiness. The full row-level reference inventory is in `PHASE1_REFERENCE_INVENTORY.csv`; proposed changes are in `PHASE1_PROPOSED_DATASET_CHANGES.md`. The machine-readable audit remains `dataset_audit.json`.
