# Post-Phase-6 quality remediation

20 October 2026. Targeted implementation changes; the five application pages, FastAPI, SQLite, hybrid retrieval implementation and the two selected generative checkpoints are preserved. No gold evaluation examples were added as application rules. No legal review or real-user acceptance results are claimed.

## 1. Missing-slot root causes

The historical grouped-test F1 **0.280** is unchanged and was not rerun. The 1,444 grouped test rows and the gold evaluation cases were not used for remediation fitting, rule design or new scoring. Previous exposure of the test set remains a limitation; no independent final test is available.

The paired development diagnostic uses **4,634 grouped training rows and 1,156 development rows**. Status phrase vocabulary comes only from grouped train. The original inference sources were frozen before edits in `experiments/manifests/remediation_nlp_baseline_sources.json`. The manifest SHA-256 is `8563a1d4d1e9682bd9acbe2bf80a2adce650ed65167d1aee3b644a5d9b312614`.

| Development diagnostic | Before | Final |
|---|---:|---:|
| Missing-slot precision | 0.1712 | 0.2286 |
| Recall | 0.7913 | 0.7913 |
| F1 | 0.2814 | 0.3547 |
| TP / FP / FN | 254 / 1,230 / 67 | 254 / 857 / 67 |
| Exact missing-set accuracy | 16.96% | 37.89% |
| Intent errors | 0 / 1,156 | 0 / 1,156 |
| Oracle entities + intent F1, diagnostic only | 0.6978 | 0.6978 |

This is development improvement, not new held-out performance. There are **321 labelled missing-slot instances**. Intent errors do not explain this development set's slot failures: oracle intent gives identical scores. Supplying annotated entities isolates an additional schema/label disagreement; it is not an attainable independent performance estimate.

Before: 758 false positives arose when the extractor missed a supplied annotated slot; 319 arose from normalization, unresolved ambiguity or conflict; 153 persist even with annotated entity presence. After: those counts are 385, 319 and 153. All 67 false negatives concern labels outside the schema's required rows. The generic conditional trigger `only_when_relevant_to_rule_or_situation` is not executable legal logic; no predicate or ground truth was invented to turn it into one.

Largest FP slot counts before → final: USER_ROLE 386 → 72; VEHICLE_CLASS 368 → 368; INJURY_PRESENT 108 → 85; CHALLAN_DATE 75 → 68; RC_STATUS 57 → 44; STATE 57 → 57. Informal bus/bike/truck categories can remain genuinely ambiguous under the formal vehicle vocabulary and still need clarification. False negatives include USER_ROLE 22, RC_STATUS 10, DEATH_PRESENT 9, INSURANCE_STATUS 6, INJURY_PRESENT 5, LICENCE_STATUS 4, EVENT_DATE 3, OTHER_VEHICLE_IDENTIFIED 3, VEHICLE_CLASS 3 and STATE 2. Detailed **per-slot and per-intent** counts, predictions and causal attribution are in `remediation_nlp_before*`, `remediation_nlp_after*` and `remediation_nlp_final*` under `experiments/metrics` and `experiments/predictions`.

## 2. Slot corrections and adaptive questioning

- Added schema-scoped extraction for explicit labelled categorical/text/date facts, including user role, registration state and accident context. Shared words such as “valid” and “yes” are scoped by a fact label. Generic questions are not turned into affirmative role/injury facts.
- Extended specialized date normalization and explicit destination-state handling; retained source spans and unknown states. Added road vocabulary, explicit role statements, received-challan normalization, cancellation/registration states, and word-boundary status checks so “invalid” cannot become “valid”.
- Made conversational recomputation call the same slot detector as NLP analysis, eliminating duplicated requirement logic. A provided resolved conditional fact no longer leaves that same slot marked unresolved. Explicit conditional requirements can be passed to the detector; unspecified legal conditions and the AGE schema gap remain unresolved.
- Moved production status vocabulary to the grouped training partition. Missing local classifier artifacts were rebuilt from grouped train, not the old overlapping split. A short-input regression was addressed with **116 catalog-wide intent name/description examples**, uniformly generated from all 58 ontology entries, with no evaluation-case routing rules. The final runtime classifier is also checked on development only and has zero intent errors there.

Ground-truth missing-slot labels, required-slot rows and ambiguous vehicle normalization were not weakened. A schema/annotation review and more robust general extraction are still needed. The changed language-template unit test now verifies membership in the actual Hinglish schema templates instead of demanding particular words from a particular question; no NLP evaluation labels were edited.

## 3. LLM rejection causes, both models

Every one of the **18 archived raw generations** was inspected, including all six original Llama failures and eight original Mistral failures. Per-output original and replay verdicts are retained in `remediation_llm_archive_audit_final_*.jsonl` and summarized in [the failure appendix](remediation_llm_failures.md). The archived evidence-package bytes and original Phase 6 outputs are unchanged.

| Archived finding | Llama 3.2 3B | Mistral 7B v0.3 |
|---|---:|---:|
| Original accepted / generated | 3 / 9 | 1 / 9 |
| Original fallback | 6 / 9 | 8 / 9 |
| Literal claim linkage rejection | 3 | 5 |
| Original definite-outcome flags | 3 | 3 |
| Missing cited claim | 0 | 1 |
| Original final language rejections | 3 | 4 |

Reason counts overlap and should not be summed into failure counts. The six definite-outcome flags were caused by the model copying a server limitation containing “penalty is asserted”, not six established liability claims. Other linkage failures include copying a question or “Relevant provision” as a claim, capitalization/punctuation differences, and English claim text attached to different Hindi prose. Hindi requests frequently produced English answers. Several purported Hinglish answers were entirely English; the old gate did not reject that. One originally accepted Mistral Hindi answer contained mixed-script/misleading wording and an English explanation, illustrating why citation IDs do not establish semantic support or translation quality.

All archived outputs parsed with the required fields and known citation IDs. No invalid JSON, missing required fields, invalid evidence IDs, numeric-claim rejection, runtime exception or visibly incomplete JSON was recorded in this sample. The old adapter did not retain finish reasons, so absence of a truncation flag alone is not proof of a correct runtime stop. Unsupported suggested actions were omitted (five Llama actions and two Mistral actions); deterministic actions remained authoritative. Omitted legal qualifications/translation meaning require qualified review; no independent semantic acceptance rate is claimed.

## 4. Prompt, output handling and measured effects

Implemented shared prompt `remediation-grounded-v3`: short prose, literal claim copying after writing the prose, exact citation identifiers, explicit Hindi/Hinglish instructions, preservation of exceptions, and no unsupported procedures/numbers/outcomes. The prompt includes the actual Pydantic schema.

The Ollama adapter now passes a schema derived from `Explanation.model_json_schema()` in `format`, rather than plain JSON mode, matching [Ollama's structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs). The shared per-request schema fixes the language code, constrains citation IDs to the supplied evidence, and constrains actions to supported titles (an empty array if none exist); downstream checks still run. Both checkpoints use temperature 0, 700 output tokens by default, seed 471 and an 8,192-token context. The output cap was not inflated without truncation evidence. A length stop is rejected as OUTPUT_TRUNCATED. The parser rejects duplicate keys and nonstandard JSON constants; it does not manufacture missing fields or repair a claim into acceptance.

Production and development retests now share the same language gate, checking both answer and explanation. Roman-script Hindi indicators are required for Hinglish; this is a coarse mismatch gate, not a fluency assessment. Empty model uncertainty is rejected when evidence carries limitations; deterministic limitations continue to be appended. A narrowly scoped outcome correction exempts only **exact server-supplied uncertainty strings** from the lexical outcome detector. Generated prose, claims, actions, changed uncertainty and the entire numeric/section/ID/linkage checks remain gated. Regression tests reject genuine definitive claims even beside the exempt limitation.

| Final check | Llama | Mistral |
|---|---:|---:|
| Archived outputs passing current stricter replay | 1 / 9 | 0 / 9 |
| Planned frozen-evidence development cells | 9 | 9 |
| New generated outputs | 0 | 0 |
| New generation acceptance rate | **Unavailable** | **Unavailable** |
| Runtime-unavailable cells requiring fallback | 9 / 9 | 9 / 9 |

The replay is **not new inference or a new model-performance score**. It falls because the stronger language gate rejects previously accepted English-only Hinglish and mixed-language Hindi explanations. Both new-inference retests are blocked because local Ollama is unreachable; no model executable was installed and no replacement generative model was introduced. The frozen development set remains three synthetic cases × English/Hindi/Hinglish, identical evidence and parameters for both checkpoints. Evidence SHA-256: `0664014e964b86683b9aa7412f1e1711c6ea86fc7b420cff131a016c2f3fdbf3`. Run `scripts.remediation_llm_dev --run-id <new-run>` when those exact local checkpoints are available; the script preserves prior outputs.

The validators remain conservative structural safeguards. They are not a semantic entailment proof: unsupported unenumerated legal prose can still escape pattern checks. Improving this requires a reviewed support protocol and qualified multilingual/legal review; **this limitation is not fixed or disguised as legal correctness**.

## 5. Legal coverage and review boundary

Before → after: **4 / 11 eligible provisions → 4 / 11**, **0 affirmative procedures → 0**, **0 eligible numeric penalties → 0**, **0 reviewed numeric speed limits → 0**. The repaired procedure is parseable (29 → 30 procedure records) but remains NOT_VERIFIED and excluded. The speed table now has explicit NOT_VERIFIED record flags rather than silently lacking a review column; no existing substantive cell was changed.

The [qualified-review queue](remediation_legal_review.md) details all seven unavailable provisions, authoritative lookup evidence, specific substantive discrepancies and proposed review actions. `experiments/metrics/remediation_legal_current.json` lists every procedure, offence, speed and provision record with physical row, source ID, reasons and resolution category. The BNS subsection (1) paraphrase incorrectly imports a reporting condition; its correction is proposed, not silently published. Subsection (2) stays excluded pending commencement evidence. The 2019 amendment source requires section-specific commencement and review, not a blanket source flag. Numeric speed rows need category/road/date/signage reconciliation. No missing legal source ID was guessed.

The system can responsibly provide qualified general licensing, registration, speed-regulation and insurance information from the four eligible dataset records after date/jurisdiction/fact confirmation. It cannot determine guilt, actual fines, road-specific numeric limits, deadlines, or affirmative administrative/court procedures from this corpus. Existing dataset VERIFIED labels do not establish independent legal correctness.

## 6. PDF export verification

Implemented: printable source IDs and full URLs, all sources and fact-law mappings instead of arbitrary slices, and generation method/model/checkpoint/digest/timestamp/language/fallback/prompt/index/evidence/source-fingerprint provenance. Printing waits for fonts. Print sections can paginate and long references wrap. Hindi font fallbacks were added.

The Print / Save as PDF control was invoked. The in-app browser's action timed out and exposed no save dialog; native Chrome automation was subsequently stopped on uncertain URL verification despite user approval. Later, `report.pdf` appeared in the workspace with title NyayaSaarthi and producer Microsoft: Print To PDF. Its creation route was not independently established. **All five pages were rendered and visually inspected** using the bundled PDF renderer. The artifact contains all five confirmed facts, readable Hindi narrative/car label, EVID:PROV_MVA_S112, government source URL, all three uncertainty statements and deterministic generation provenance. No missing glyphs or omitted content were observed. PDF extraction returns no text on all five pages, so this artifact is not text-searchable through the tested extractor.

The saved artifact splits fact labels from values between pages 1/2 and splits provenance across pages 2/3. Targeted print keep-together blocks and explicit text for empty mappings/procedures were implemented. **A fresh browser export after those pagination changes remains NOT VERIFIED** because computer use had stopped. The inspected artifact also records the earlier lexical test index, not the final rebuilt hybrid index. It is preserved unchanged as an observed export artifact, not presented as a newly rendered final-code PDF. See `experiments/metrics/remediation_pdf_inspection.json` for its SHA-256 and page-by-page inspection evidence.

## 7. Mobile and frontend reliability

A real production-browser journey traversed all five pages at **320 × 740** through FastAPI and isolated SQLite. Home, Understand, Verify, Guidance and Summary each reported document scroll width **305 px** within a 320 px viewport: no horizontal page overflow was observed. Hindi text was visually readable in the conversation. Five individual confirmations were persisted, a source was retrieved and the matter reached Summary. This initial browser run used an explicitly labelled lexical-only test index; it is not hybrid retrieval verification or a user acceptance audit.

The browser exposed a cramped brand/language/progress header and a mobile navigation button without an action. Both were patched; the menu now exposes the existing routes with expanded-state semantics. A real Guidance snapshot also filtered production fact identifiers through mock IDs and hid the facts; it now displays real confirmed facts. These final three fixes pass build/type/lint checks, but **post-fix browser rechecks were blocked by the computer-use stop**. Other mobile widths, final menu keyboard behavior, desktop layout and refreshed Summary persistence were not newly verified in this run.

Other implemented reliability fixes: real-mode session restore rejects stale demo records and malformed cache objects; blocked/full session storage does not crash backend-persisted work; real guidance's mock-generation path is explicitly demo-gated; unavailable model options stay disabled; stored model/language choices restore from backend metadata; header language selectors now share the real intake state; fallback provenance distinguishes requested language from actual English output, and language-review limitations no longer contradict a requested model translation; stale answer recovery checks HTTP status rather than text; guidance loading errors expose a retry action. The current five-page architecture was preserved.

## 8. Files modified

See the generated changed-file inventory at the end of this report. Core changes are in NLP extraction/normalization/slot detection/conversation, shared LLM handling, frontend state/guidance/summary/header/styles, two CSV technical repairs, dependency lockfile, runtime-artifact metadata, regression tests and new reproducible remediation scripts/evidence. The two classifier artifacts are local ignored build products, reproducible from `scripts.remediation_runtime_artifacts`; generative model checkpoints were not changed.

## 9. Checks actually executed

- Full backend suite: **46 passed** on the final code/corpus, including extraction, contradiction handling, stale revision checks, legal exclusion, provider-schema/truncation, duplicate JSON, language and genuine-vs-server-uncertainty outcome regression checks.
- Development NLP: frozen-original baseline; one extraction-development run; final runtime-classifier run. Each uses 1,156 dev rows; no new grouped-test or gold-case scores.
- Corpus audits before, after procedure repair, and final schema repair; per-record exclusion manifests preserved. Whole-dataset validation reports 20,214 parsed rows, one remaining critical error (OFF_NO_PUC source reference), and 341 warnings; these are not hidden or counted as passing legal review.
- All 18 archived LLM outputs audited/replayed; both nine-cell new development retests attempted and recorded as runtime blocked. `scripts.check_models` confirms both configured tags are unavailable because Ollama is unreachable.
- Six real isolated HTTP journeys: deterministic, Llama-requested and Mistral-requested against the labelled lexical test index, then the same three modes against the **actual rebuilt hybrid index**. Each reached COMPLETED, retrieved one eligible record, persisted guidance, checked stale revisions and unknown answers. Both model-requested modes used deterministic fallback; these are availability/fallback smokes, **not successful inference**.
- True hybrid functional smoke: final index `15930382a608885b`, source fingerprint `90f62bfb87ba4215d287af4cac7348f82ac69f69cc965db9c7643040e3c56309`, four admitted provisions, three successful lexical-plus-semantic queries, and abstention without date/jurisdiction. This is functional verification, not a fresh retrieval relevance score. The existing multilingual MiniLM embedding model was preserved.
- Frontend ESLint, TypeScript `--noEmit`, and production `next build`: passed after final frontend edits under bundled Node 24.19.0 / Next.js 16.3.4. All five routes build. The initial `npm ci` failed due to inconsistent transitive lockfile entries; the lockfile was repaired and `npm ci --dry-run --ignore-scripts` subsequently passed. `.venv` is excluded from repository lint.
- `git diff --check`: passed after restoring the procedure file's newline style.
- Browser observations as described above, retained in `experiments/metrics/remediation_browser.json`. The browser test backend/database are isolated and ignored by Git. The code changes were not deployed.

## 10. Status and remaining issues

| Status | Issue and evidence |
|---|---|
| FIXED | Schema-scoped fact extraction and shared adaptive slot recomputation; measured FP reduction 1,230 → 857, development F1 0.2814 → 0.3547; regression suite passes. |
| FIXED | Structured-output request, truncation rejection, strict JSON parsing, shared language checks and exact-server-uncertainty outcome false positive; adapter/security regressions pass. Real-model benefit remains unmeasured. |
| FIXED | Procedure CSV alignment and missing speed review column; 30 parsed procedures, zero review promotions, eligibility remains 4/11 with no numeric/procedural claims. |
| FIXED | Frontend dependency lockfile; final lint/typecheck/build and clean-install dry-run pass. |
| PARTIALLY FIXED | Missing slots: 857 FP and 67 FN remain; ambiguity, general extraction, vague condition schemas and 220 schema/label disagreements remain. No ground truth was weakened. |
| PARTIALLY FIXED | LLM acceptance and legal support: prompt/adapter/gates improved, but no new inference acceptance rate and no semantic legal proof. Exact citation IDs alone are insufficient. |
| PARTIALLY FIXED | Frontend/PDF/mobile: code fixes and one real five-page 320px journey completed; final header/menu/language-selector/fact-snapshot browser rechecks and a fresh PDF after the pagination corrections remain outstanding. |
| BLOCKED | Real Llama/Mistral development inference: local Ollama unreachable; 0 generated outputs, 18 runtime-blocked cells, safe fallback preserved. |
| BLOCKED | Fresh native PDF re-export after the observed pagination fixes: computer-use service stopped on uncertain current browser URL despite the user's explicit Chrome-access approval. A previously saved five-page artifact was inspected without further UI automation; no safety mechanism was bypassed. |
| BLOCKED | Corpus expansion: missing authoritative references, provision-specific commencement and qualified legal review. Proposed corrections are review inputs only. |
| NOT VERIFIED | Fresh final-code PDF pagination and hybrid-index provenance in an export, final patched mobile menu/header/language-selector/snapshot behavior, other mobile sizes, refreshed Summary, independent legal/translation correctness, real-user acceptance and untouched final-test performance. Saved-artifact content/Hindi rendering were verified as described above. |

Hybrid verification is in `experiments/metrics/remediation_hybrid_smoke.json` and `remediation_hybrid_http_*.json`; the execution manifest is `remediation_checks.json`. No Library upload capability is exposed in this session; these reports and evidence are saved in the project workspace.

## Changed-file inventory

Tracked edits and newly created remediation evidence; ignored dependencies, databases, indexes and classifier binaries are excluded. The observed `report.pdf` was inspected but not modified.

- `.gitignore`
- `README.md`
- `backend/README.md`
- `backend/app/services/conversation.py`
- `backend/app/services/legal/guidance.py`
- `backend/app/services/llm/explanation_service.py`
- `backend/app/services/llm/grounding_validator.py`
- `backend/app/services/llm/local_runtime.py`
- `backend/app/services/llm/output_checks.py`
- `backend/app/services/llm/prompt_builder.py`
- `backend/app/services/llm/provider.py`
- `backend/app/services/llm/response_parser.py`
- `backend/app/services/nlp/entity_extractor.py`
- `backend/app/services/nlp/normalizer.py`
- `backend/app/services/nlp/slot_detector.py`
- `backend/artifacts/intent_model_metadata.json`
- `backend/artifacts/language_model_metadata.json`
- `backend/experiments/manifests/remediation_nlp_baseline_sources.json`
- `backend/experiments/manifests/remediation_procedure_repair.json`
- `backend/experiments/manifests/remediation_procedure_repaired_row.txt`
- `backend/experiments/manifests/remediation_python_environment.txt`
- `backend/experiments/manifests/remediation_speed_review_schema.json`
- `backend/experiments/metrics/remediation_browser.json`
- `backend/experiments/metrics/remediation_checks.json`
- `backend/experiments/metrics/remediation_dataset_validation.json`
- `backend/experiments/metrics/remediation_http_deterministic.json`
- `backend/experiments/metrics/remediation_http_llama3.2-3b.json`
- `backend/experiments/metrics/remediation_http_mistral-7b.json`
- `backend/experiments/metrics/remediation_hybrid_http_deterministic.json`
- `backend/experiments/metrics/remediation_hybrid_http_llama3.2-3b.json`
- `backend/experiments/metrics/remediation_hybrid_http_mistral-7b.json`
- `backend/experiments/metrics/remediation_hybrid_smoke.json`
- `backend/experiments/metrics/remediation_legal_after.json`
- `backend/experiments/metrics/remediation_legal_before.json`
- `backend/experiments/metrics/remediation_legal_current.json`
- `backend/experiments/metrics/remediation_legal_final.json`
- `backend/experiments/metrics/remediation_llm_archive_audit.json`
- `backend/experiments/metrics/remediation_llm_archive_audit_final.json`
- `backend/experiments/metrics/remediation_llm_dev.json`
- `backend/experiments/metrics/remediation_llm_dev_final.json`
- `backend/experiments/metrics/remediation_nlp_after.json`
- `backend/experiments/metrics/remediation_nlp_before.json`
- `backend/experiments/metrics/remediation_nlp_before_causes.json`
- `backend/experiments/metrics/remediation_nlp_final.json`
- `backend/experiments/metrics/remediation_nlp_final_causes.json`
- `backend/experiments/metrics/remediation_pdf_inspection.json`
- `backend/experiments/pdf_preview/page-1.png`
- `backend/experiments/pdf_preview/page-2.png`
- `backend/experiments/pdf_preview/page-3.png`
- `backend/experiments/pdf_preview/page-4.png`
- `backend/experiments/pdf_preview/page-5.png`
- `backend/experiments/predictions/remediation_llm_archive_audit_final_llama3.2-3b.jsonl`
- `backend/experiments/predictions/remediation_llm_archive_audit_final_mistral-7b.jsonl`
- `backend/experiments/predictions/remediation_llm_archive_audit_llama3.2-3b.jsonl`
- `backend/experiments/predictions/remediation_llm_archive_audit_mistral-7b.jsonl`
- `backend/experiments/predictions/remediation_llm_dev_final_llama3.2-3b.jsonl`
- `backend/experiments/predictions/remediation_llm_dev_final_mistral-7b.jsonl`
- `backend/experiments/predictions/remediation_llm_dev_llama3.2-3b.jsonl`
- `backend/experiments/predictions/remediation_llm_dev_mistral-7b.jsonl`
- `backend/experiments/predictions/remediation_nlp_after.jsonl`
- `backend/experiments/predictions/remediation_nlp_before.jsonl`
- `backend/experiments/predictions/remediation_nlp_final.jsonl`
- `backend/reports/post_phase6_remediation.md`
- `backend/reports/remediation_legal_review.md`
- `backend/reports/remediation_llm_failures.md`
- `backend/scripts/phase6_dataset_overlay.py`
- `backend/scripts/remediation_legal_audit.py`
- `backend/scripts/remediation_llm_dev.py`
- `backend/scripts/remediation_nlp_dev.py`
- `backend/scripts/remediation_runtime_artifacts.py`
- `backend/scripts/run_llm_smoke.py`
- `backend/tests/test_conversation.py`
- `backend/tests/test_legal_phase4.py`
- `backend/tests/test_llm_phase5.py`
- `backend/tests/test_remediation.py`
- `data/Dataset 2/procedures.csv`
- `data/Dataset 2/speed_limits.csv`
- `eslint.config.mjs`
- `package-lock.json`
- `report.pdf`
- `src/app/globals.css`
- `src/components/guidance/GuidanceWorkspace.tsx`
- `src/components/guidance/SituationSnapshot.tsx`
- `src/components/home/HeroSection.tsx`
- `src/components/layout/Header.tsx`
- `src/components/summary/SummaryWorkspace.tsx`
- `src/components/understand/UnderstandHeader.tsx`
- `src/components/understand/UnderstandWorkspace.tsx`
- `src/lib/matter-storage.ts`
- `src/providers/MatterProvider.tsx`
- `src/types/matter.ts`
