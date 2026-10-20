# Phase 6 implementation record and viva architecture

Phase 6 repaired training/test vocabulary leakage, added a reproducible connected scenario/template split, evaluated NLP and three retrieval rankers, froze synthetic admissible evidence, ran controlled local LLM comparisons, tightened structured output and action handling, added offline ablations, and exercised an isolated persisted HTTP workflow. The original datasets and source admissibility policy were preserved. This is a working local research demonstrator with documented legal and evaluation gaps, not a publicly deployed legal service.

## Architecture in order

1. A lightweight character TF-IDF SVM identifies likely intent because it is reproducible on limited local hardware; a language baseline and script policy choose a language or abstain.
2. Rule-based extraction keeps exact original-text offsets. Normalization maps spans to dataset IDs. Intent-specific slot rules identify required context and unresolved conditional requirements.
3. Adaptive questions select missing slots; user answers, contradictions, edits and provenance persist in SQLite. The user must confirm facts and explicitly verify the structured situation before retrieval.
4. Hybrid RAG combines BM25 and multilingual semantic rankings over policy-eligible provisions. Date/jurisdiction gates and structured rule evaluation determine what may be said; a ranked match alone is not a legal conclusion.
5. Deterministic guidance builds source cards, uncertainties and next steps. Llama 3.2 3B or Mistral 7B may rewrite only a frozen eligible-evidence package. Schema, citation, language, numeric-claim and definite-outcome gates reject unsafe output; fallback preserves deterministic guidance.
6. Both models are compared on the same three synthetic matters × three languages. Offline ablations measure recorded context gain, ranker contribution and rule-exposure proxy; they do not yield one unified full-system score.

See `nlp_results.md`, `retrieval_results.md`, `llm_comparison.md`, `ablation_study.md`, `failure_analysis.md`, `legal_coverage.md`, `final_system_evaluation.md`, and `deployment_readiness.md` for measured evidence. Human review of legal support and multilingual usefulness, stronger missing-slot labels, additional eligible sources, completed PDF export, and mobile visual QA remain outside the completed evidence.
