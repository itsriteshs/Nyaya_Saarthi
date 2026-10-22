# Intake and Guidance remediation — 22 October 2026

## Inspection and actual causes
Read repository AGENTS.md and installed Next.js client-component documentation. Working tree was clean at the start. Traced Home preview and persisted analyze APIs → NLP pipeline → SLM extractor → atomic matter adapter → conversation planner; verified-matter generate API → deterministic hybrid evidence → frozen package → Ollama → parser/language/grounding checks → saved guidance → Guidance and Summary display. No legal CSV records changed.

Both configured models are currently installed and available: Llama3.2:3b-instruct-q4_K_M and Mistral:7b-instruct-v0.3-q4_K_M. Read-only SQLite inspection found current ordinary matters with eight Llama and one Mistral INSUFFICIENT_ELIGIBLE_EVIDENCE rejections; prior QA matters also contain RUNTIME_UNREACHABLE. The historical remediation_llm_failures.md records UNLINKED_CLAIM for both models. Initial stored matters did not establish UNSUPPORTED_SPEED_FIGURE. A new real frozen-evidence development generation DID reproduce UNSUPPORTED_SPEED_FIGURE for Llama; Mistral timed out. These are distinct causes and are not reported as successful model generations.

## Corrections
- SLM remains primary for initial and follow-up extraction. A numeric speed without a unit is retained with normalized numeric candidate, unit=unknown and unresolved status. The planner asks for the unit, not another number. A subsequent km/h answer reconciles the existing candidate with provenance/history. A different number creates an unresolved contradiction, including when the initial candidate lacked a unit.
- Informal road wording maps to OTHER when no existing category is justified. Original quote is stored separately as sourceText. Location context remains LOCATION. In a road-type answer, a supported location without a precise category can accompany an OTHER road category, preserving the location rather than rejecting the answer repeatedly. OTHER does not assert a specific legal road classification.
- Grounding/normalization uses literal source spans. Case-only differences can be reconciled against the original text. Short-message structured decoding restricts quote/value to literal input spans; atomic short road answers must echo their wording, preventing model-generated OTHER/free_text from replacing it. This is a general extractive schema constraint, not a phrase-routing regex.
- Uncertain categorical slot assignments outside the explicitly requested slot are retained as unassignedMentions in extraction metadata, not asserted as facts or turned into extra optional questions. Ambiguous values and numeric/date uncertainty remain available for clarification. Exact text grounding cannot independently prove semantic attribution; user verification is still essential.
- Logs showed prompt processing and generation exceeding a minute, with20s client aborts. Reduced intake prompt verbosity; default inference budget is now60s, capped90s; matching frontend intake timeouts100s. Existing contention fallback remains. Cold loading and CPU contention can still exceed those bounds.
- Evidence packages now carry confirmed fact units/source text. A reported speed may be repeated only as a complete, exact, language-specific attributed sentence generated from a confirmed resolved fact with known km/h units. Legal claims, actions and uncertainty receive no numerical exemption. Unconfirmed, different-valued, unitless or threshold figures remain blocked. Penalty/deadline/section/outcome/citation checks remain effective.
- Verbatim claim linkage remains mandatory. Prompt now asks for a direct qualified answer, confirmed-fact relationships, accessible evidence explanation, material limits and supported steps. It does not call a provision a judgment. The same exact claims and eligible source links are rendered together in Guidance and Summary. Both views explain uncertainty, supported steps and understandable specific fallback causes. No supported procedure means no invented action.

## Live evidence and limits
intake_guidance_live_recheck.json preserves the first actual model runs and paired frozen-evidence Guidance results. intake_main_road_diagnostic.json records raw model output that invented OTHER/free_text instead of extractive values, motivating constrained decoding. That diagnostic alone used60s override; metadata retains the configured20s and explicitly records the override. Earlier failed attempts remain archived. intake_final_validated_live.json records final intake checks, when complete; do not interpret earlier failures as passing.

These are reused development scenarios, not untouched evaluation or human acceptance. No increase in held-out NLP score or model acceptance rate is claimed. Valid citation IDs and substring linkage are structural checks, not independent legal correctness. The real Llama rejection and Mistral timeout remain unresolved generation-quality/performance cases. No model was substituted, no legal record promoted and no absent evidence was fabricated.

## Verification
Full suite at the intermediate revision:107 passed in64.54s. Final affected-suite and frontend results are appended below. Tests cover missing unit, unit-only reply, conflict preservation, informal road/location context and OTHER; short-answer schema; valid/invalid citations, exact claim linkage, attributed reported speed versus legal thresholds, unsupported penalties/deadlines/sections/outcomes, missing uncertainty, unavailable runtime, parser/language failures and no eligible evidence without any generation call. Existing intake tests cover issue-confirmation persistence, multilingual text, dates and fallback.

No new browser layout, browser export, or independent legal review was performed in this turn. UI was checked through lint/typecheck/build; visual browser review remains NOT VERIFIED. Runtime setup is local Ollama with the two exact configured tags; intake defaults to Llama, Guidance uses the selected model. Missing runtime, missing evidence, malformed/schema-invalid output, citation/linkage, numeric/legal grounding, language, truncation and timeout failures still intentionally return deterministic guidance.

## Status
FIXED in implementation/tests: candidate preservation/unit-only clarification; conflict retention; safe OTHER plus original context; constrained extractive short answers; attributed speed distinction; claim/source report display and reason explanations.
PARTIALLY FIXED: model semantic accuracy, generation schema compliance and performance; resource-aware bounded runtime improves opportunity but cannot guarantee acceptance.
BLOCKED/UNRESOLVED: real Guidance Llama speed rejection and Mistral timeout in the recorded recheck; evidence coverage remains unchanged and limits answers.
NOT VERIFIED: final independent model quality, untouched evaluation, human acceptance, fresh browser/mobile/PDF behavior.

## Files modified
backend/.env.example
backend/app/schemas/matter.py
backend/app/services/conversation.py
backend/app/services/llm/evidence.py
backend/app/services/llm/grounding_validator.py
backend/app/services/llm/prompt_builder.py
backend/app/services/nlp/slm_extractor.py
next-env.d.ts
src/components/guidance/DirectAnswer.tsx
src/components/summary/SummaryWorkspace.tsx
src/lib/api/conversations.ts
src/lib/api/matters.ts
src/lib/api/nlp.ts
src/types/matter.ts

New files: backend/tests/test_intake_guidance_revision.py; src/components/guidance/GroundedReportDetails.tsx; this report and live diagnostic JSON evidence.

## Final live intake result
All three final checks invoked local Llama and returned local_slm without fallback: unitless120 retained unresolved with unknown unit; Main road accepted as OTHER; school-zone answer accepted with raw wording preserved. Metadata and entities are in intake_final_validated_live.json. That run preceded the final general OTHER→separate LOCATION copy, which is covered by the final added regression. The model sometimes emits a categorical guess from a question; unassigned categorical diagnostics remain visible in metadata and are not treated as asserted facts.

Final affected suite before the last context-copy regression:51 passed in56.73s. Final lint/typecheck/build results and full-suite result follow below.

Legal-data integrity check: git diff --name-only -- *.csv returned no changes. No legal dataset record was modified. All changes remain in the existing architecture.

Final full backend suite:109 passed in76.66s. Final frontend ESLint and TypeScript typecheck passed before production compilation. No fresh browser/mobile/export verification is claimed.

Final Next.js production build passed, including TypeScript and all five application routes.
