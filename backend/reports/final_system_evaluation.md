# Phase 6 final system evaluation

The isolated local HTTP journey created a synthetic matter, persisted real NLP analysis, edited and confirmed facts, verified the user context, retrieved one admissible provision when date and jurisdiction were supplied, generated guidance, reloaded persisted guidance and completed the matter. A second synthetic matter answered an adaptive question with an explicit unknown, which remained in the persisted conversation. Stale revision and pre-verification guidance requests returned 409. Llama and Mistral end-to-end runs invoked real inference and fell back safely; a deterministic run completed without fallback. All five routes return HTTP 200 and build under Next.js 16.3.4. One interactive browser journey passed through Home, Understand, Verify, Guidance and Summary with real persisted backend state, confirmed five extracted facts, selected Llama, displayed one eligible source and safe fallback, and restored Summary on refresh without console errors. An earlier refresh exposed a hydration mismatch; restoring tab state after hydration fixed it. The print button and print CSS are present, but a completed PDF export and mobile visual QA were not verified.

| Evidence | Result |
|---|---|
| Grouped utterance split | 4,634 train / 1,156 dev / 1,444 test; previous test exposed. |
| Intent / entity / missing-slot F1 | 100.0% / 92.8% / 28.0%. |
| Language overall with abstentions | 90.3%, coverage 90.3%. |
| Hybrid retrieval | Recall@1 77.5%, MRR 0.870 on 1,162 admitted-positive queries. |
| Legal source coverage | 4 eligible provisions; no admissible numeric penalty, speed limit or affirmative procedure. |
| LLM safety | See `llm_comparison.md` for actual accepted/fallback rates; semantic support remains unreviewed. |

The measured NLP and retrieval results are exploratory because reference labels are unreviewed and the earlier test partition was exposed. Browser observations are recorded in `experiments/metrics/phase6_browser_e2e.json`; isolated HTTP run details are in adjacent metrics files. The main functional limits are missing-slot precision, sparse legal coverage and multilingual model acceptance. No public deployment was attempted because matter endpoints have no authentication.
