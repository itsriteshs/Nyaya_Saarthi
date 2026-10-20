# Phase 6 offline ablations

These component comparisons use different case sets and are **not** a single full-pipeline score. Safety controls remain active in production.

| Component comparison | Sample | Measured outcome |
|---|---:|---|
| Initial utterance vs recorded final conversation | 450 conversations, 1350 required-slot observations | Captured coverage 31.4% → 81.8%, +50.4 points; 749 recorded questions; redundant recorded question rate 0.0%; mean 1.66 turns. |
| Current first-question policy vs recorded first question | 450 | Agreement 97.1%. |
| BM25 only vs semantic only vs hybrid | 1162 answerable queries | Recall@1 57.3% / 65.5% / 77.5%. |
| Retrieval without a matched structured rule | 3 frozen matters | 33.3% retrieved sources lack a matched rule; proxy exposure only. |
| Deterministic vs Llama/Mistral | 9 generations per available model | Structural acceptance and fallback in `llm_comparison.md`; human usefulness difference N/A. |

Final conversations were recorded in source data, not newly produced by the app, and no unknown user fact was assumed. The rule proxy does not claim retrieval-only actually emitted an unsupported legal conclusion. A deterministic comparison cannot establish a quality gain without blinded judgments. Figures: `experiments/plots/adaptive_context.png`, `retrieval_comparison.png`, `llm_comparison.png`.
