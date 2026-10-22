# SLM-first intake — 22 October 2026

## Implementation and trace

Read AGENTS.md and the installed Next.js client-component guide before frontend changes. Home's debounced preview calls `/nlp/analyze`; submit creates a DRAFT matter then calls `/matters/{id}/analyze`. Both use `nlp.pipeline.analyze` → **`slm_extractor.interpret`** → existing local `OllamaProvider` → `/api/chat`. This is a new intake integration, independent of Guidance. The production default attempts **Llama 3.2 3B Instruct**, runtime name `llama3.2:3b-instruct-q4_K_M`. `NYAYA_INTAKE_MODEL=mistral-7b` selects the existing `mistral:7b-instruct-v0.3-q4_K_M` instead. No third generative model was introduced.

Messages over16,000 characters conservatively fall back with INTAKE_CONTEXT_TOO_LARGE rather than silently truncating. The trained language/intent classifiers still supply suggestions. The intake SLM receives the complete message and catalog-wide slot definitions, not just slots for the suggested issue. It returns strict structured JSON with slot, exact supporting quote, extractive value, certainty and approximation. It cannot set legal conclusions, normalized IDs, confirmation flags or arbitrary fields. Successful model extraction is primary; deterministic extraction runs only on disabled/unavailable/busy/timed-out/invalid/empty model output. No situation-specific phrase rules were added.

`matter_adapter.persist_analysis` stores all returned entities and metadata before `conversation.initialize` plans the first question and commits atomically. Facts retain original supporting text, normalized value/ID, extraction method, source message, approximation, uncertainty and unconfirmed status. Conflicting initial values persist separately with unresolved contradiction records. Issue confirmation retains those facts. The existing planner sees normalized facts and skips sufficiently resolved slots.

Follow-up fact answers use the same SLM-first extractor, with the target slot as context. Explicit issue choices and “I don't know” answers retain deterministic control handling. Other supported facts in a reply now persist even when its requested target is absent or ambiguous; previously that early return discarded them. Scoped fact edits remain deterministic explicit user corrections. Date-slot remapping no longer overrides an explicitly extracted matching date slot.

## Grounding and safety boundaries

- Strict Pydantic JSON contract rejects unknown fields/types and unsupported slots. Quotes must occur exactly in the message and values exactly within quotes. Invalid/empty payloads fall back as a whole.
- Model-authored translations, dates, numerical values and canonical IDs cannot silently become user-stated facts. Normalization uses the existing vehicle/jurisdiction vocabularies, literal slot values, supported speed-unit validation and conservative date parsing. Unrecognized translations or values remain unresolved for confirmation.
- General assertion-scope validation marks negated/hypothetical clauses unresolved, even when the model quotes only an isolated positive word. This is a conservative validation guard, not a growing scenario classifier.
- General date parsing adds ISO, day/month/year, day-month-year, day.month.year and English named months. Ambiguous numeric dates need clarification. English/Hindi/Hinglish relative-day normalization uses a timezone-aware supplied reference only; bare `kal`/`कल` remain ambiguous. No reference means no inferred relative date. These are documented parsing/normalization needs, not UAT phrase routing rules.
- `LOCATION` preserves school-zone context without guessing a legal road subclass. The supported extraction contract adds informational **POLICE_INVOLVEMENT** text because the existing schema has no equivalent: it explicitly does **not** mean POLICE_REPORTED, an issued challan, a charge or an applicable legal rule. No legal CSV, eligibility or grounding validator was changed.
- Exact spans are necessary but cannot independently prove semantic attribution, completeness or the truth of a user's statement. User verification remains mandatory; extracted facts alone establish no legal conclusion. Existing emergency safety detection and fail-closed legal retrieval remain intact.

## Runtime setup and observable fallback

Run local Ollama at `http://127.0.0.1:11434` with the selected exact runtime model name from `model_registry.py` installed. `ollama list` should show that name; `ollama serve` starts the local service if the installation requires it. No model downloads or installations were performed by this change. Project example configuration now documents:

```text
NYAYA_INTAKE_SLM_ENABLED=true
NYAYA_INTAKE_MODEL=llama3.2-3b
NYAYA_INTAKE_TIMEOUT=20
```

Set these in the backend environment/startup configuration; merely editing `.env.example` does not set process variables. Existing NYAYA_OLLAMA_URL and local-only runtime checks apply. Timeout is clamped to 1–30s, max output 1600 tokens, temperature0, existing seed471/context8192. A bounded extraction gate permits one active local inference and up to3s waiting; contention falls back with INTAKE_BUSY. Intake frontend requests now allow40s so the backend's bounded inference can finish or return fallback. Preview and submit may each trigger extraction; preview cancellation does not cancel server-side inference, and cold model loading may exceed the intake budget.

Analysis persists `extractionMetadata` with requested model/runtime/checkpoint, whether generation was actually called, method, fallback flag, failure reason, prompt version and successful latency/digest. Follow-ups store per-message extractionHistory. The existing preview warning exposes deterministic fallback. A requested model is never proof it actually generated a response.

**Live check:** the actual pipeline attempted local runtime discovery, received RUNTIME_UNREACHABLE and returned deterministic facts without failing. `modelCalled=false`, method=deterministic_fallback. Ollama was absent from PATH and its usual per-user installation location; that does not prove absence from every possible installation directory. The example's car and approximate130km/h survive fallback, but school-zone and police context are not captured by the old deterministic extractor. They are verified through the simulated SLM contract/integration tests only. Real model extraction quality is BLOCKED pending runtime/model availability; no real SLM success or acceptance rate is claimed. Evidence: `slm_intake_live_smoke.json`.

## Tests and verification

94 backend tests passed, including32 focused new intake tests. New tests use simulated provider responses; two adapter tests exercise both model choices through the actual Ollama adapter with simulated HTTP replies. They demonstrate wiring, validation, persistence and planner behavior, not real-model paraphrase/language accuracy. They cover the requested example; paraphrases; Hindi/Hinglish; multiple facts; explicit/relative/ambiguous dates; missing reference; unsupported and invented values/fields; empty/malformed output; unavailable runtime, timeout and truncation; negation; conflicts; issue confirmation; follow-up extra-fact preservation; and user-verification gates.

Final checks: 94 backend tests passed in17.33s; frontend ESLint passed; TypeScript typecheck passed; Next.js production build passed; git diff --check passed. No new browser test, untouched NLP test evaluation, legal review or human usability study was performed for this change.

## Changed files for this implementation

- backend/app/services/nlp/slm_extractor.py (new primary extraction/validation/normalization adapter)
- backend/app/services/nlp/pipeline.py (intake integration and fallback warning/metadata)
- backend/app/schemas/nlp.py and backend/app/schemas/matter.py (analysis/fact metadata)
- backend/app/services/conversation.py (follow-up integration, preservation, fact provenance)
- backend/tests/test_slm_intake.py and backend/tests/conftest.py (focused contracts; normal regression tests explicitly disable optional runtime)
- backend/.env.example (intake configuration)
- src/lib/api/nlp.ts, matters.ts, conversations.ts (bounded intake request timeouts)
- this report and slm_intake_live_smoke.json (actual evidence)

FIXED: primary intake and follow-up integration, grounded extractive contract, metadata/persistence and planner preservation, tested with simulated model outputs and real fallback. PARTIALLY FIXED: varied-phrase/language interpretation depends on actual model responses and conservative normalization; omissions and semantic misattribution remain possible. BLOCKED: real-model end-to-end quality verification. NOT VERIFIED: browser behavior for slow real inference and all language/date variants. Architecture, selected generative models and legal-safety gates preserved.
