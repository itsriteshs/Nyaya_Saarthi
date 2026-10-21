# Current recheck — 21 October 2026

New issue selection is catalog-driven and user-labelled, retains original model output and does not hardcode evaluation queries. Synthetic scenario-to-issue choices exist only in test scripts as test-user replies. No classifier weights, gold labels, legal review flags or grounding validators were weakened. See [UAT_RECHECK_REPORT.md](UAT_RECHECK_REPORT.md) and [UAT_RECHECK_SCENARIOS.csv](UAT_RECHECK_SCENARIOS.csv) for evidence and limitations. The earlier audit below is retained as historical evidence.

---

# Hardcoding and mock audit

Confirmed user-visible prototype leakage: HeroSection initialized analysisInput with defaultSituation although the textarea was empty; empty submission also substituted the active topic example. Both now use empty input in real mode and require user text or an explicitly chosen example. Stale preview facts clear during new input analysis. This was real backend inference on an undisclosed sample, not a mocked model response; it still misrepresented whose facts were analyzed.

SituationSummary used demo IDs vehicle_type/speed/location and always said "You reported driving". Real-mode summary now lists actual facts without assuming role.

Remaining demo modules: src/lib/mock-context-engine.ts, mock-nlp.ts, mock-legal-retrieval.ts. HeroSection and UnderstandWorkspace gate demo behavior with NEXT_PUBLIC_NYAYA_DEMO_MODE===true; GuidanceWorkspace demo generation is gated and guarded against real nlpAnalysis matters. matter-storage rejects stale demo cache in real mode. Constants/static labels/deterministic conservative fallbacks remain legitimate. Selected generative models unchanged. No evaluation examples were installed as application rules. Full mutation suite remains incomplete; no blanket absence-of-hardcoding certification.

Browser regression confirmed empty-submit validation after stalled print tab closed. Removed inert sidebar Settings and placeholder My Matters rather than adding unrelated features.
