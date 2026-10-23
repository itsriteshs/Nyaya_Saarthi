# Intake fallback policy

SLM interpretation remains primary. Busy runtime, unavailable model, timeout, truncation, invalid output or disabled extraction uses existing deterministic extraction and normalization. No new phrase patterns or legal records were added.

The ordinary fact-review flow has no technical fallback warning. Output is not labeled as SLM-generated when the model did not produce it. extractionMetadata records method, fallbackUsed, failureReason, modelCalled, entityCount and fallbackLatencyMs. Fact methods retain their actual extractor provenance; user confirmation remains required. Other uncertainty warnings and legal safety checks are retained.

The checkout already contained fallback code. The previous SLM-only error string was absent from this checkout, so the running backend was reloaded to avoid stale code.

Checks: 35 focused intake tests passed; full backend suite 100 passed. Added busy-gate direct/API/follow-up persistence and empty-fallback tests. Existing timeout/unavailable/malformed-output and successful SLM tests pass. A Guidance fallback regression previously relied on the developer having no running Ollama; it now explicitly simulates model unavailability. These are controlled tests, not new model-quality measurements. No frontend code changed.

Live check after restart: POST /api/v1/nlp/analyze returned HTTP 200. The real SLM response failed source grounding (UNGROUNDED_MENTION), so deterministic fallback supplied USER_ROLE, VEHICLE_CLASS, OBSERVED_SPEED and ROAD_TYPE. Metadata correctly recorded fallbackUsed=true; no technical fallback warning was returned. This is one runtime smoke check, not an extraction quality benchmark.
