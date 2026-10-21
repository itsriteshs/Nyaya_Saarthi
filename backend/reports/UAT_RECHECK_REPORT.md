# UAT remediation recheck — 21 October 2026

The original 10 FAIL / 10 PARTIAL scorecard is historical. After implemented corrections, all 20 synthetic workflows have a positive functional outcome in both the actual browser and HTTP rechecks: **19 complete Home → Understand → Verify → Guidance → Summary, and S18 is safely rejected as outside supported scope**. These are user-assisted workflows, not 20 unconditional acceptance passes. The user explicitly confirms the issue and supplies missing facts. Automatic intent accuracy, independent legal correctness and unavailable model outputs are not established by completion.

## FIXED — implemented and checked

- Uncertain intent now asks for issue confirmation before issue-specific questions. The user can select any supported domain/intent or outside scope. User selection is labelled as such; the original prediction remains in the audit record. S18 cannot proceed to legal review even by acknowledging unknowns. No UAT text-to-intent overrides were added.
- Clause-scoped document statuses, explicit Hindi State aliases, injury negation and explicit witness-role extraction repair missed or crossed facts. Licence-entitlement LMV/MCWG spans no longer become the incident vehicle. General canonical class IDs and codes are accepted without guessing an unspecified truck's legal class.
- Optional ambiguous facts previously caused a deadlock: the frontend demanded resolution while the backend offered no question. They now receive a clarification question, including which vehicle a multi-vehicle account concerns. S10–S12 reach Summary in the browser. This does not establish full multi-party accident modelling.
- Multi-fact replies preserve additional supported facts. Date/State operational requirements are explicit, corrections resolve existing conflicts only, and newly detected contradictory facts require a separate resolution. S15 tests contradiction resolution and S17 vehicle correction; persisted facts and guidance equal their GET representations in every completed HTTP journey.
- Home now waits for hydration before accepting input, preventing filled text from disappearing. Empty real-mode input and corrected Verify facts remain repaired. The five-page architecture is preserved.
- Deterministic generation records requested/actual language and evidence-package provenance. Hindi requests transparently fall back to English; no fake Hindi output is claimed. Summary preserves user clarification notes separately from legal evidence and states primary-issue scope.
- Actual Copy Summary succeeded: 2,460 clipboard characters with evidence, uncertainty, provenance and scope. Copy rejection/timeout also has a selectable manual-copy recovery. The forced-failure UI branch was not exercised.
- Build validation caught and corrected the clipboard timer type and lint scanning of generated QA output. Final lint, TypeScript typecheck and production build pass. Backend: **62 tests passed in 13.91 seconds**.

## Measured missing-slot quality — PARTIALLY FIXED

The historical grouped-test F1 **0.280** remains unchanged and was not rerun or used for tuning. Reused synthetic development data: **4,634 training / 1,156 development records, zero test records evaluated**. Earlier development F1 **0.3547486** becomes **0.3525281**, with 251 TP, 852 FP and 70 FN; exact-set accuracy 0.3762976. This is a small regression, not a claimed metric improvement.

Largest current slot errors are VEHICLE_CLASS (368 FP / 3 FN), USER_ROLE (76 FP / 25 FN), INJURY_PRESENT (85 FP / 5 FN), CHALLAN_DATE (68 FP / 0 FN), STATE (57 FP / 2 FN), and RC_STATUS (44 FP / 10 FN). Coarse vehicle mentions versus exact legal subclasses remain a normalization/schema mismatch. Unsupported role/injury assertions and dates/statuses account for additional extraction and requirement errors. There are **67 gold missing-slot entries absent from or nonrequired by their intent schema**. Labels were retained. Even oracle entities plus oracle intent reach only F1 0.6978022, demonstrating label/schema/conditional requirement problems beyond extraction.

There are zero intent errors on this reused synthetic development partition, while real-language UAT inputs have wrong predictions. Existing character SVM, word SVM and word+character SVM each score 1.0 development accuracy/macro F1. None was promoted based on UAT performance. Representative reviewed development data and an untouched final evaluation are still required. The issue-confirmation workflow improves safe usability without pretending the model itself improved.

## LLM output — BLOCKED for real inference

Both selected models are preserved. Six real generation-endpoint requests used three documented contexts (S01 speeding, S05 insurance, S11 accident), identical frozen evidence within each model pair and comparable settings: temperature 0, seed 471, 700 output tokens, 8,192 context tokens, structured Explanation schema. Confirmed facts remained unchanged.

All six used deterministic fallback: four RUNTIME_UNREACHABLE and two INSUFFICIENT_ELIGIBLE_EVIDENCE. Ollama reports both models unavailable. There were **zero actual model inferences**, so neither a new real acceptance rate nor a Llama/Mistral quality comparison can be reported. Historical 3/9 and 1/9 acceptance are not superseded. Prior failure classifications and structured-output work remain documented in remediation_llm_failures.md and post_phase6_remediation.md; this turn did not relax grounding checks or change the selected models.

## Legal coverage — BLOCKED for substantive expansion

Before and after: **4/11 eligible provisions** (sections 3, 39, 112, 146); zero eligible affirmative procedure, numeric penalty or numeric speed-limit records. No review flags or legal records were promoted in this recheck. remediation_legal_review.md and experiments/metrics/remediation_legal_current.json retain the record-by-record exclusion/review queue and prior technical repairs. General qualified licensing, registration, insurance and speed-regulation information is available where evidence supports it. Exact fines, road-specific limits, deadlines, affirmative procedures, guilt and independent legal correctness remain outside demonstrated coverage. Valid evidence IDs alone do not establish a legally correct answer.

## Reliability — PARTIALLY FIXED

Local retrieval/model initialization caused a measured first request of 134.064 seconds. A singleton initialization lock, bounded Torch threads and default startup warm-up move loading before request acceptance. Warm requests and all final journeys complete. Cold startup remains slow and environment-dependent; this is not resolved as a performance issue. Initialization failures still fail closed.

## Mobile and PDF

**Mobile verified in the actual browser:** a fresh Hindi S03 full journey completes at measured CSS viewport **320 × 800**. Home, Understand, Verify, Guidance and Summary have document/body scroll width 305, no horizontal overflow. Screenshots and accessibility states are archived. This is targeted layout verification, not a complete accessibility, keyboard, contrast, device or all-scroll-position audit. Hindi rendering is present in the journey; a complete Hindi typography audit is not claimed.

**PDF saved-file export is BLOCKED / NOT VERIFIED.** The earlier in-app print invocation stalled browser interaction and exposed no Save as PDF interface; native Chrome access/URL restrictions prevented completing that alternative. No new saved PDF exists and no export-content/rendering success is claimed. The visible/clipboard Summary includes actual facts, evidence, references, uncertainty and generation provenance; that is not proof of a PDF containing them.

## Evidence and tests actually executed

- uat_recheck_browser.json: all 32 attempts preserved, including earlier failures and later fixes; latest result per S01–S20 is in UAT_RECHECK_SCENARIOS.csv. No failed attempt was deleted.
- uat_recheck_after_http.json: final current-code 20-scenario create/analyze/clarify/confirm/verify/guidance/complete/persistence run. An intermediate reporting-file Windows lock interrupted a prior run; the harness now writes the report once, and the full run succeeded.
- uat_recheck_mobile_journey.json, uat_recheck_mobile_layout.json and qa_screenshots/recheck-*-mobile.jpg: fresh 320-CSS mobile evidence.
- uat_recheck_copy.json: actual clipboard content checks; qa_screenshots/recheck-summary-desktop.jpg: actual completed Summary.
- uat_recheck_model_fallbacks.json: six real endpoint attempts, frozen evidence IDs, settings, runtime failures and fallback metadata.
- remediation_nlp_uat_recheck_scoped_final.json and associated predictions: final development evaluation; uat_recheck_dev_changes.json: earlier per-record changes; uat_intent_dev_candidates.json: development-only classifier experiment.
- Full backend pytest suite: 62 passed; frontend ESLint and TypeScript: passed; Next.js production build: passed (all five application pages generated). No untouched held-out test was rerun.

## Remaining status separation

**FIXED:** concrete workflow deadlocks, factual extraction/correction defects listed above, hydration race, response persistence shape, summary provenance/notes/copy, lint/type errors; backed by unit, HTTP and targeted browser checks.

**PARTIALLY FIXED:** intent/OOD behavior made user-confirmable but automatic generalization remains weak; missing-slot quality remains low and development F1 slightly regressed; multi-party attribution remains limited; cold-start latency moved before serving but remains long; language fallback is transparent but Hindi generative quality is untested.

**BLOCKED:** actual Llama/Mistral inference (Ollama unavailable), substantive legal expansion (authoritative review required), native PDF save in available browser environment.

**NOT VERIFIED:** freshly saved PDF content/rendering; independent legal correctness; independent human usability/acceptance; untouched final NLP performance; comprehensive accessibility/all-device coverage; forced clipboard-error recovery UI.

The application is improved for a supervised deterministic workflow. It is not ready to claim full unsupervised legal or bilingual-model acceptance.

## Files changed

See UAT_RECHECK_FILES.txt for the current workspace change inventory. Some files include prior audit changes; the inventory is not a claim that every diff originated in this recheck. No new legal dataset or trained model was promoted. Reports are saved locally; no ChatGPT Library upload tool is available in this session.

QA cleanup: this recheck stopped its own frontend3002 and backend8012 after verification. Ordinary user servers were not targeted.
