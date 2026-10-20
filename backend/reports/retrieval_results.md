# Phase 6 retrieval results

The hybrid index version is `a6183dd22a43ad0b`; source fingerprint `b0521a641e94c970ab3b12b41f66357705feae5acbcf0d3d84cc9dc21ed2cb2c`. An isolated offline rebuild using the saved local embedding checkpoint reproduced the same index version, 4 documents and model revision. The admitted corpus contains only 4 provisions. We ranked the same corpus for 2,159 distinct queries; 1,162 had an admitted positive and 997 had only an excluded positive. No query-specific jurisdiction, date, or domain filter was applied in this ranking experiment. Production retrieval still applies eligibility, jurisdiction and date filters.

| Ranker | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| BM25 | 57.3% | 73.2% | 75.6% | 0.648 |
| Semantic | 65.5% | 97.2% | 100.0% | 0.806 |
| Hybrid RRF | 77.5% | 96.9% | 100.0% | 0.870 |

Hybrid improves Recall@1 over BM25 by 20.1 percentage points and MRR by 0.222; semantic is slightly higher at @3. Recall@5 is weakly informative with only four eligible provisions. Precision@k is **N/A** because most admitted query-document pairs are unjudged. All relevance labels are pending human review; this is a ranking result, not a legal applicability or answer-quality score. Per-query rankings are saved in `experiments/predictions/phase6_retrieval.jsonl`; figure: `experiments/plots/retrieval_comparison.png`.
