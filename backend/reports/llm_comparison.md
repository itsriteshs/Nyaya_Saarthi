# Phase 6 real local LLM comparison

Both models receive identical frozen synthetic evidence packages, prompts (`phase6-grounded-v2`), English/Hindi/Hinglish requests, temperature 0 and output cap. Ollama applies each checkpoint's own chat template. One trial per case-language cell; no seed is exposed by the adapter. Each model has three cases × three languages. Generation latency is measured separately from offline retrieval. Input packages and raw outputs are in `experiments/manifests/phase6_evidence_packages.json` and `experiments/predictions/`.

| Model | Generations | Structurally accepted | Fallback | Median generation latency | Mean output tokens |
|---|---:|---:|---:|---:|---:|
| llama3.2-3b | 9 | 33.3% | 66.7% | 4.96 s | 185.1 |
| mistral-7b | 9 | 11.1% | 88.9% | 18.54 s | 298.1 |

- **llama3.2-3b** — Ollama `llama3.2:3b-instruct-q4_K_M` (Q4_K_M), installed digest `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`. English/Hindi/Hinglish structural acceptance: 33.3%/0.0%/66.7%. Rejection reason counts: {'DEFINITE_OUTCOME': 3, 'UNLINKED_CLAIM': 3}; unsupported actions omitted: 5. Mean latency 5.81 s; p95 8.34 s.
- **mistral-7b** — Ollama `mistral:7b-instruct-v0.3-q4_K_M` (Q4_K_M), installed digest `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf`. English/Hindi/Hinglish structural acceptance: 0.0%/33.3%/0.0%. Rejection reason counts: {'DEFINITE_OUTCOME': 3, 'UNLINKED_CLAIM': 5, 'INSUFFICIENT_CITED_EVIDENCE': 1}; unsupported actions omitted: 2. Mean latency 20.95 s; p95 37.36 s.

| Model | Known citation IDs (proxy) | Unsupported actions omitted | Grounding rejected | Language rejected | Semantic claim support |
|---|---:|---:|---:|---:|---:|
| llama3.2-3b | 100.0% | 5 | 3 | 3 | N/A |
| mistral-7b | 100.0% | 2 | 4 | 4 | N/A |

Acceptance requires parsed schema, requested language, known evidence IDs, literal claim linkage and absence of prohibited numeric or definite claims. Unsupported model-suggested actions are omitted; deterministic next steps remain authoritative. Citation validity is a **structural proxy**. A valid citation does not prove a semantically supported legal claim. No blinded human legal or multilingual quality ratings took place, so comparative usefulness, factual support and fluency are **N/A**. Each model's metrics file includes language-specific outcomes and reason codes. Figure: `experiments/plots/llm_comparison.png`.
