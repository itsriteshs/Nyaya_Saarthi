# Current recheck — 21 October 2026

Uncertain issue selection precedes topic questions. All 20 scenarios were repeated through their appropriate end state; multi-fact replies, explicit unknowns, contradiction resolution and vehicle correction were exercised. Exact vehicle subclass ambiguity and low missing-slot development F1 remain. See [UAT_RECHECK_REPORT.md](UAT_RECHECK_REPORT.md) and [UAT_RECHECK_SCENARIOS.csv](UAT_RECHECK_SCENARIOS.csv) for evidence and limitations. The earlier audit below is retained as historical evidence.

---

# Adaptive questioning UAT

Sparse scenario1 started at0/3, wrongly on illegal-parking workflow. It asked event date. Answer2026-10-19 recovered date (1/3), then asked State. One reply "A car on an expressway in Tamil Nadu" recovered all three explicit entities; relevant wrong-workflow required coverage became2/3. It then asked specific location. Useful recovery exists, but cannot compensate for wrong intent.

Detailed scenario2 extracted car,80km/h,city road,Tamil Nadu,yesterday and required no follow-up:3/3, shown99% because a conditional requirement remained unresolved. Chennai was missed. These two inputs selected different schemas, so their slot coverage is not directly comparable as a quality score.

Scenario20 recovered car from a later answer (2/3 to3/3), then all five facts were individually confirmed. Refresh preserved confirmation. Guidance and Summary used those five facts. Unknown/refusal loops, correction/contradiction turns and duplicate requests were not repeated through browser in this audit; existing backend tests cover related behavior but do not establish browser acceptance. No new missing-slot F1 or held-out metric claimed.
