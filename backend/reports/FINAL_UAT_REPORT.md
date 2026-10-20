# Final UAT report — NOT READY

Audit performed 2026-10-20 using synthetic browser-created matters only. This is an agent-operated acceptance audit, not independent human user testing or held-out NLP evaluation.

## Scope and results
All 20 core inputs submitted through the actual Home interface and completed initial Understand inspection. Only scenario20 continued through Verify, Guidance and Summary; scenario1 included delayed date and multi-fact replies. The other journeys are explicitly incomplete. Baseline core results: 0 PASS, 10 FAIL, 10 PARTIAL. Two additional model-path checks BLOCKED. These are conservative acceptance classifications, not an NLP accuracy metric. PASS requires all requested assertions verified; FAIL means an observed material defect; PARTIAL means only a subset checked; BLOCKED means a required external capability unavailable. No blocked test counted as passed.

Backend 0.1.0, Next.js16.3.4, Windows, ChatGPT IAB browser (exact engine version unavailable). Separate SQLite backend/experiments/final_uat.db on8012 and QA frontend3002. Existing ports3000/8000 and ordinary user matters were not used for test mutations. Hybrid index15930382a608885b, 4 eligible provisions. The requested model checkpoints and grounding gates were preserved. Both model endpoints report runtime_unreachable. No new model acceptance rate exists.

## Significant findings and repairs
- Emergency detection missed bleeding and matched negated injury. Repaired independent mention/negation handling and added prominent server-supplied assistance alert. Backend positive/negative variants pass; browser regression of alert remains NOT VERIFIED.
- Real-mode Verify prose assumed driving and looked up demo fact IDs. Replaced with recorded fact labels/normalized values, preserving unresolved markers. Browser recheck incomplete.
- Empty real-mode Home analyzed/submitted an undisclosed example. Removed sample substitution and clear stale previews on input changes. Empty initial view visually verified after change; empty-submit browser assertion incomplete.
- Explicit age wording and Hindi spelled-out speed units/bike were missed. General span rules repaired; unit and live HTTP regressions recorded. Hindi intent and State remain weak.
- Training-vocabulary status match crossed clause boundaries. Scoped cue matching to the same clause, with regression.
- Windows Turbopack crashed when Tailwind scanned a changing backend evidence file (OS error32). Limited source scanning to src; dev homepage recovered. Source configuration follows https://tailwindcss.com/docs/detecting-classes-in-source-files .

## Unresolved high defects
Intent model selected Illegal Parking for sparse speed, Digital Licence for Hindi speeding, Licence Seized for expiry, interstate NOC for PUC, Traffic Speeding for bleeding accident, and an insurance workflow for pasta. No scenario-specific overrides or test-set tuning added. Proper remediation needs a broader domain/OOD and intent-clarification development design with separate evaluation; the current workflows remain unacceptable for unsupervised legal use. Multiple vehicles are flattened into one vehicle slot; witness/participant attribution remains unreliable. Several explicit facts remain unstructured. These findings are escalated here rather than relabelled passes.

## Evidence and limitations
FINAL_USER_SCENARIOS.csv contains observed states; qa_browser_observations.json contains actual accessibility snapshots (one initial transient snapshot retained for transparency), qa_observations.json contains 36 persisted synthetic matters at baseline capture. Scenario1 narrative records its manually observed result. Screenshots were captured in tool output and summary-mobile.jpg archived. Report records what ran, not a claim that every control or full scenario passed.

Print control invoked a browser interaction that timed out; no new saved PDF was available. Post-print automation did not reliably activate some controls; remaining browser regressions, full control inventory, fresh PDF, clipboard content, keyboard accessibility and all requested error cases are NOT VERIFIED. Initial Copy displayed Copied, but clipboard API returned empty; this is unresolved rather than proof of successful copy. Original summary evidence remained consistent. Official IndiaCode fetch timed out, so independent legal correctness is not certified.

## Verification
50 backend tests passed (8.71s). Final lint/typecheck/build outcomes are recorded below after completion. No grouped test set or gold labels were changed or re-evaluated. No legal record was promoted.

## Decision
NOT READY. Core service and a conservative deterministic five-page journey operate, but intent/OOD failures, incomplete acceptance coverage, unavailable real models and legal coverage gaps prevent final acceptance.

## Status separation
FIXED (code plus regression): injury mention/negation detection; explicit age/Hindi speed spans; status clause isolation.
PARTIALLY FIXED: emergency prominence, factual Verify prose, empty-input sample leakage, stale preview, development-file scanning; code implemented but remaining browser assertions listed above.
BLOCKED: real paired Llama/Mistral generation (Ollama unreachable); live source authentication (official source fetch timeout); fresh native PDF export in this browser environment.
NOT VERIFIED: complete remaining scenario journeys; all-control/accessibility/error matrix; clipboard contents; final PDF pagination; independent human/legal review. Never substitute these with unit test results.


## Final regression addendum
Closing the print-stalled tab restored browser interaction. Empty-submit validation then visibly passed. Bleeding now displays urgent assistance above routine questions in browser; negated-injury variation displayed no emergency warning. Explicit-age19 browser variation displayed AGE19, with learner intent. Verify on a new Kerala70km/h variant listed actual vehicle, speed, road, State and date without assumed driver prose; original speed units are preserved alongside normalization. Settings click was reproduced inert; placeholder Settings and My Matters entries were removed, and their absence verified after refresh. These revisions supersede earlier browser-incomplete notes for those specific checks, not the remaining full journeys.

Six additional live HTTP speed/State mutations passed structured fact assertions (60/100/140km/h x Kerala/TamilNadu), recorded in qa_mutations_http.json. Three post-fix live HTTP extractions are in qa_postfix_http.json. These are not browser tests or an independent NLP metric. Additional browser variants: bleeding, negated injury, age19, fully specified Kerala70. Core baseline classifications remain frozen. Browser-workflow helpers are in tests/e2e/browser-workflows.mjs; the saved helper suite itself has not been executed as a standalone runner. No complete Playwright acceptance-suite pass is claimed.

Exact browser engine version was not exposed by the allowed DOM evaluator. Window sizes and rendering constraints are in the UI report. Production build completed successfully after initial fixes; final checks are appended separately. Library upload capability was not available; requested documents are saved locally.

Live HTTP mutation analysis latency: min0.0034s, max0.0272s across6 sequential local requests. This excludes browser debounce, rendering and model generation. Full latency matrix not measured.

Security observation: a fresh unauthenticated HTTP client could read the synthetic QA matter by UUID (HTTP200). This is a local unauthenticated prototype, not an isolated public multi-user service. No public deployment or authentication claim made.

Additional modified source files: backend/app/services/conversation.py; backend/app/services/nlp/entity_extractor.py; backend/app/services/nlp/normalizer.py; backend/tests/test_conversation.py; backend/tests/test_remediation.py; next.config.ts; src/app/globals.css; src/components/home/HeroSection.tsx; src/components/understand/ConversationPanel.tsx; src/components/understand/AppSidebar.tsx; src/components/verify/SituationSummary.tsx; .gitignore. Next generated next-env.d.ts and tsconfig.json updates during builds/QA dev. New reports/evidence and tests/e2e/browser-workflows.mjs are listed by git status.


## Final executed checks and current status
- pytest backend/tests -q:50 passed in8.71s.
- Frontend eslint src next.config.ts:passed after correcting effect state handling.
- TypeScript noEmit:passed; final next build independently reran TypeScript successfully.
- Final next build:passed, compiled4.9s, TypeScript3.3s, all five routes present.
- git diff --check:passed (line-ending warnings only).
- Six live HTTP controlled speed/State variations:passed; three additional HTTP extraction observations saved.
- Actual browser confirmations, refresh persistence, retry, all five pages and initial20 inputs executed; further controls/print limits stated above.

Current FIXED: injury negation/bleeding detection and alert placement (browser observed); empty Home hidden sample/empty-submit guard (browser observed); factual Verify prose (browser observed); explicit age and Hindi speed/vehicle recognition (unit/HTTP; age browser); status clause scoping (unit/HTTP); inert sidebar controls removed (browser observed); CSS source scanning crash fix (dev recovery plus final build).
PARTIALLY FIXED: broader multilingual understanding and context recovery; material wrong intents and role/vehicle attribution remain unresolved and escalated. No model-generalization improvement claimed.
BLOCKED: paired real LLM inference; independent official source authentication; actual saved browser PDF export.
NOT VERIFIED: all remaining full scenario journeys; comprehensive controls/error/accessibility suite; actual clipboard content and final PDF pagination; independent human and qualified legal acceptance. Final audit remains incomplete against the requested definition of done; NOT READY is an acceptance rejection, not a claim of comprehensive completion.

QA-only servers8012/3002 stopped at end. Existing user servers8000/3000 left untouched.
