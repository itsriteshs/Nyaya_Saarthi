# NLP exploratory evaluation

- Model: tfidf-intent-v1
- Manifest SHA-256: 3242531df2c74cf557c307722ab56253ff73be8d1817e833c5bf56b780ace07b
- Derived test rows: 1000; processed: 1000
- Intent accuracy: 0.9240
- Intent macro F1: 0.9339
- Intent weighted F1: 0.9343
- Language accuracy: 0.5970
- Entity exact-span F1: 0.9188
- Missing-slot F1: 0.3232
- Gold cases: 420; template overlap with derived train/dev: 0
- Mean inference latency: 1.16 ms across 1000 cases

## Limits

- Synthetic templating can inflate held-out results despite template exclusion.
- Digit-masked template matching does not detect all paraphrases.
- Every utterance has pending human review.

Full per-intent metrics, confusion matrix, language breakdown, entity-type results, and sample counts are in `nlp_evaluation.json`.
