# Implemented algorithms and publication placement

These summarize existing code; they are not new legal methods.

Algorithm 1 — Incident processing (Methodology)
1. Normalize Unicode for character-based intent prediction; preserve original text.
2. Apply script-aware language policy and trained language classifier with abstention.
3. Invoke the configured local SLM for quoted facts. Validate schema, source spans and supported slots.
4. Normalize validated values, preserve ambiguity and interpretation notes; fail visibly on SLM errors.
5. Persist all facts before initializing the conversation planner.

Algorithm 2 — Adaptive clarification (Methodology)
1. Keep uncertain issue confirmation separate from collecting facts.
2. Reconcile existing normalized facts and conditional requirements.
3. Resolve conflicting or missing required slots in configured priority order.
4. Store the selected question and its available rationale.
5. Interpret each answer through intake; preserve unknowns/conflicts; ask only remaining questions.
6. Require user fact review before legal guidance; invalidate guidance after revisions.

Algorithm 3 — Eligible retrieval (Methodology)
1. Select confirmed facts, jurisdiction, event date and candidate domains.
2. Load the frozen local index; reject records failing source/date/jurisdiction/domain policy.
3. Compute BM25 and multilingual embedding similarity ranks.
4. Fuse ranks using RRF k=60, returning scores, sources and exclusions.
5. Evaluate supported structured rule conditions against confirmed facts; preserve unresolved results.

Algorithm 4 — Grounded generation (LLM design)
1. Construct deterministic source-linked baseline from eligible evidence and rule traces.
2. Build a bounded evidence package with confirmed facts and server-authored limitations.
3. If evidence or runtime is absent, retain deterministic fallback and record reason.
4. Otherwise invoke the selected Llama or Mistral tag with structured JSON output.
5. Validate schema, requested language, citations, literal claim linkage, prohibited numbers and outcomes.
6. Persist accepted output with provenance; otherwise retain baseline and failure metadata.

Algorithm 5 — Offline evaluation (Experiments/Ablation)
1. Create an immutable run ID; snapshot code, dependencies and model hashes.
2. Filter manifest train/dev rows before evaluating labels; never retune grouped test.
3. Apply controlled variants to identical cases and settings, saving case predictions.
4. Calculate denominator-explicit metrics and available uncertainty intervals.
5. Separate failed, unavailable, synthetic, archived and reviewed results.
6. Generate publication figures/tables from the same JSON read by the dashboard.

Use intent and language figures in Results; source eligibility and retrieval in Legal Retrieval; LIME coefficients/fidelity/stability in Explainable AI; R0–R3 outputs in Ablation only with the explicit proxy and review caveats. No model-based legal correctness or hallucination rate was measured.

Architecture: citizen inference remains separate from offline research. Timeline reconstruction is not shown as an independent implemented model. Numeric penalties/procedures remain withheld when source eligibility is absent.
