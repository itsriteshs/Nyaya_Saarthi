# Phase 1 verification and remediation review

This compares the original Phase 1 audit (8 errors, 315 warnings) with the expanded validator run (2 errors, 341 warnings, 6 informational standalone queries). The source datasets remain unchanged. A row number is the physical CSV line, including the header at line 1. The full 143 placeholder and 28 currently missing-reference findings, with source record IDs and context, are in `PHASE1_REFERENCE_INVENTORY.csv`.

## The original eight critical findings

| File:line | Column / exact original value | Classification | Explanation |
|---|---|---|---|
| `procedures.csv:26` | Record `PROC_CONTEST_ECHALLAN_COURT`: 21 CSV fields versus 22 headers; there is no field at the `deadline` position. The next field is `Court filing fee (nominal, State-specific)`. | Corrupted CSV structure | The missing field shifts `fee_rule` and subsequent fields left. The row cannot be safely imported. The raw 21-field array is preserved in `dataset_audit.json`. |
| `offences_penalties.csv:31` | `source_id = ""` on `OFF_NO_PUC` | Unresolved required relationship | There is no source ID for this offence and its `provision_id` is also `PROV_CMVR_PUC_PENDING_ADD`. Do not use its penalty text as verified legal guidance. |
| `query_provision_relevance.csv:4470` | `query_id = Q_SYN_PROV_MVA_S39_1` | Incorrect validation rule | A standalone synthetic query has `query_text` in this row; it is not an `annotated_utterances.utterance_id`. |
| `query_provision_relevance.csv:4471` | `query_id = Q_SYN_PROV_MVA_S39_2` | Incorrect validation rule | Same standalone synthetic-query convention. |
| `query_provision_relevance.csv:4472` | `query_id = Q_SYN_PROV_MVA_S39_3` | Incorrect validation rule | Same standalone synthetic-query convention. |
| `query_provision_relevance.csv:4473` | `query_id = Q_SYN_PROV_MVA_S177_1` | Incorrect validation rule | Same standalone synthetic-query convention. |
| `query_provision_relevance.csv:4474` | `query_id = Q_SYN_PROV_MVA_S177_2` | Incorrect validation rule | Same standalone synthetic-query convention. |
| `query_provision_relevance.csv:4475` | `query_id = Q_SYN_PROV_MVA_S177_3` | Incorrect validation rule | Same standalone synthetic-query convention. |

The validator now reports the six synthetic query IDs as `STANDALONE_QUERY_ID` information and requires nonempty local `query_text`. It still flags their `intent_id = NOT_VERIFIED` as six unresolved placeholders. Eight apparent missing document references were also misclassified: the values are `FORM_*` IDs present in `official_forms.csv`, stored under `required_document_ids`. They now produce `REFERENCE_TYPE_MISMATCH` warnings. The two genuinely unresolved missing references are `FORM_33` in `procedures.csv:12` (`required_form_ids`) and `AGE` in `intents.csv:17` (`conditional_slot_ids`). No replacement ID is inferred.

## Warning groups (original 315; expanded 341)

| Category | Original | Current | Effect before later phases |
|---|---:|---:|---|
| Placeholder references | 143 | 143 | Blocks use of the affected legal rule, penalty, procedure, source, form, or relevance link as a resolved reference. Some also affect adaptive question requirements. |
| Exact text across splits | 101 audit entries | 101 audit entries | Represents **833 distinct texts** across split labels; only 100 examples plus one remainder issue are emitted as warnings. **231** texts cross splits within a single dataset, and **59** gold-test texts also occur in train rows. This blocks trustworthy NLP training/evaluation until split ownership is fixed. |
| Extra empty trailing column in `intents.csv` | 58 | 58 | Parser preserves all 58 rows. Clean CSV structure before exporting to other training tools; not an immediate API blocker. |
| Form ID in document-requirement field | 8 | 8 | Ambiguous schema for procedure document/form retrieval. Review before adaptive document questions or legal procedure guidance. All eight form IDs resolve in `official_forms.csv`. |
| Non-URL text in `official_services.official_url` | 3 | 3 | Blocks using those three rows as direct official links. The values say the URL varies by state; no URL was guessed. |
| Missing referenced records | 2 | 28 | `FORM_33` affects registration address change; `AGE` affects learner-licence conditional questioning and 26 utterance annotations. |

Review status is tracked separately rather than generating one warning per unreviewed row. Neither warning count includes the pending or unverified records below.

## Reference inventory and workflow impact

The expanded inventory contains all 143 placeholders and 28 missing references. The new 26 findings are `annotated_utterances.known_slots = AGE` for `INT016` (21 train, 3 dev, 2 test); those rows also contain `AGE` entities. This confirms the slot-schema gap affects actual NLP annotations. The 16 original apparent missing references are listed individually in `PHASE1_ORIGINAL_MISSING_REVIEW.csv`. They consisted of 6 standalone synthetic query IDs (validator rule fixed), 8 valid form IDs in document fields (namespace mismatch), and the 2 true missing references. Placeholder counts by location are:

| Dataset and field | Count | Workflow impact |
|---|---:|---|
| `document_requirements.form_ids` / `.procedure_id` / `.provision_id` | 30 / 30 / 5 | Traffic-stop, licence, registration, and accident-document flows, plus PUC/fitness and other domains. |
| `procedures.official_service_id` / `.legal_basis_provision_ids` | 24 / 2 | Licence, registration, e-challan payment, accident FIR, PUC and other procedures. |
| `accident_relief_and_claims.procedure_id` / `.provision_id` / `.scheme_source_id` | 7 / 9 / 8 | Accident assistance, cashless care, compensation, and source citations. |
| `offences_penalties.provision_id` | 15 | Licence, racing/speed-trial, enforcement, PUC, permit and other offences. |
| `rule_logic.provision_id` | 7 | Learner licence, registration transfer, accident duty, Good Samaritan, hit-and-run compensation, PUC. |
| `query_provision_relevance.intent_id` | 6 | The standalone registration and general-penalty queries lack verified intent labels. |

For the requested core workflows:

- **Speeding:** no placeholder on the general speed-limit rule is shown by this inventory. `OFF_RACING_SPEED_TRIAL` has a pending provision, but racing is a distinct offence. `speed_limits.csv` has no row-level review-status field, so its source links and dates cannot alone establish legal verification.
- **Challan:** `PROC_PAY_ECHALLAN` points to `SVC_ECHALLAN_PENDING_ADD`; `PROC_CONTEST_ECHALLAN_COURT` is the malformed CSV row. Traffic-stop document requirements have pending form and procedure links. Three synthetic general-penalty relevance queries have `intent_id = NOT_VERIFIED`.
- **Licence:** two learner-licence rules have pending legal provisions; licence procedures point to `SVC_SARATHI_PENDING_ADD`; licence document requirements have pending form/procedure links. `INT016` and 26 learner-licence utterances reference missing slot name `AGE`.
- **Registration:** the transfer-timeline rule has a pending provision; registration procedures point to `SVC_VAHAN_PENDING_ADD`; registration document requirements have pending links. `FORM_33` is missing from the form table; three synthetic registration queries have unverified intent labels.
- **Insurance:** traffic-stop document requirements include insurance context with pending form/procedure links. The inventory shows no general insurance-provision placeholder; this does not establish legal review of the whole insurance workflow.
- **Accident:** accident-duty, Good Samaritan, and hit-and-run rules have pending provisions. Accident relief has 24 placeholder links, and accident-document requirements and FIR procedure have further pending links. These block source-grounded accident guidance.

## Review status by dataset

`verified` below is an **audit label from an explicit row field**, not independent confirmation that the legal claim is accurate. `unknown` means no recognized row-level review value. `coverage_registry` status is not inherited by other rows.

| Dataset | Verified | Pending review | Not verified | Unknown | Review dimension |
|---|---:|---:|---:|---:|---|
| accident_relief_and_claims | 18 | 0 | 12 | 0 | legal/data `review_status` |
| adaptive_conversations | 0 | 0 | 3000 | 0 | `human_review_status=pending` for all; `legal_review_status=not_reviewed` for all. Composite takes stricter status. |
| annotated_utterances | 0 | 10000 | 0 | 0 | human annotation review |
| case_law_interpretations | 3 | 0 | 22 | 0 | legal/data review |
| coverage_registry | 5 | 3 | 22 | 0 | coverage metadata only |
| document_requirements | 5 | 0 | 25 | 0 | legal/data review |
| gold_evaluation_cases | 0 | 420 | 0 | 0 | `legal_reviewer=PENDING`; not human gold approval |
| intents | 0 | 0 | 0 | 58 | no review field |
| jurisdictions | 0 | 0 | 0 | 37 | no review field |
| legal_provisions | 7 | 1 | 3 | 0 | legal/data review |
| legal_sources | 7 | 2 | 9 | 0 | source review |
| offences_penalties | 17 | 1 | 12 | 0 | legal/data review |
| official_forms | 8 | 0 | 22 | 0 | legal/data review |
| official_services | 0 | 0 | 0 | 30 | no review field |
| plain_language_multilingual | 0 | 11 | 0 | 0 | legal **and** language review both pending |
| procedure_steps | 0 | 0 | 0 | 30 | no review field |
| procedures | 4 | 0 | 25 | 0 | legal/data review; one malformed row excluded |
| query_provision_relevance | 0 | 4474 | 0 | 0 | relevance judgment review pending |
| rule_logic | 13 | 2 | 15 | 0 | legal/data review |
| safety_challenge_cases | 0 | 1500 | 0 | 0 | challenge review pending |
| slot_schema | 0 | 0 | 0 | 330 | no review field |
| speed_limits | 0 | 0 | 0 | 30 | no review field |
| vehicle_classes | 0 | 0 | 0 | 30 | no review field |
| **Total parsed rows** | **87** | **16414** | **3167** | **545** | 20213 |

Only 7/18 legal sources and 7/11 provisions carry `VERIFIED`; 17/30 offence rows and 13/30 rules carry it. The 87 figure mixes these with forms, procedures, case law, accident relief, and **5 coverage-registry metadata rows**. It does not represent 87 verified NLP annotations. All 10,000 utterances are pending human review; all 3,000 conversations are pending human review and not legally reviewed. The 420 gold cases have `legal_reviewer=PENDING`.

## Matter contract and Phase 2 gate

The backend accepts the existing camelCase matter fields through PATCH, including fact provenance, answers, messages, current question, verification time, and guidance. Create returns an honest DRAFT without extracted facts. A realistic create → clarify → verify → guidance → retrieve test passes, including revision conflicts and optional-field omission. The backend allows arbitrary dataset slot strings, while current `MatterContext` has a four-slot union. `StoredMatter` now exposes that broader type and requires an explicit adapter before a backend matter can be used as UI `MatterContext`. The frontend still runs its existing mock/session flow.

**Phase 2 implementation can begin** with schema and NLP service work behind this boundary. **Model training or claims of evaluation quality should wait** for human review and split repair. Source-grounded legal retrieval remains blocked on review, missing source relationships, and workflow placeholders. No source dataset was changed.
