# Phase 2 implementation

## Pipeline and data

`app/services/nlp/pipeline.py` coordinates nondestructive Unicode normalization, language identification, intent classification, original-span extraction, normalization, and intent-specific missing-slot detection. The trained components are character TF-IDF + Linear SVM for intent and language. Intent IDs and names come from `intents.csv`; the classifier predicts all 58 dataset intents. Entity extraction is a rule and annotation-vocabulary baseline, **not** trained NER. Vehicle IDs and State/UT IDs are grounded in `vehicle_classes.csv` and `jurisdictions.csv`. `slot_schema.csv` defines required and conditional slots. The 26 AGE annotations missing from that schema receive a provisional unresolved slot; source CSVs are not rewritten.

`scripts.prepare_nlp_data` validates 10,000 annotated utterances and writes a derived manifest. It excludes digit-masked text templates overlapping a higher priority source split or the unreviewed gold cases. The source split labels remain intact. There are 7,076 train, 729 dev, 1,000 test, and 1,195 excluded rows; 175 template groups cross original split labels. This conservative template method cannot rule out every paraphrase. All 10,000 utterances await human review; the 420 gold cases await legal review and are not an independent benchmark.

## Training and evaluation

Run `python -m scripts.prepare_nlp_data`, `python -m scripts.train_intent_baseline`, `python -m scripts.train_language_baseline`, then `python -m scripts.evaluate_nlp` from `backend`. The intent comparison used word TF-IDF + Logistic Regression (0.655 seconds) and character TF-IDF + Linear SVM (2.130 seconds), each 1.000 dev accuracy and macro F1 on this templated data. The character model was selected on dev only for its spelling and transliteration features. The language model trained in 1.059 seconds. Generated models live under ignored `artifacts/*.joblib`; JSON metadata and the split manifest record versions, class labels, counts, and a SHA-256 manifest identifier.

On the untouched derived test of 1,000 unreviewed utterances, intent accuracy is 0.924, macro F1 0.934; language accuracy 0.597 with conservative abstention; exact-span entity F1 0.919; missing-slot F1 0.323. These are exploratory results. Low slot F1 reflects both extraction coverage and a mismatch between annotation missing slots and the implemented strict required-slot policy. Normalization agreement is not measurable without reviewed canonical target values. Mean warmed inference latency was 1.16 ms over 1,000 cases in a local Python 3.12 process; maximum was 203.7 ms. Full per-intent and per-entity metrics are in `reports/nlp_evaluation.json`.

## API and frontend

`POST /api/v1/nlp/analyze` returns canonical analysis without changing a matter. `POST /api/v1/matters/{id}/analyze` takes a revision, analyzes a DRAFT matter, and atomically stores `nlpAnalysis`, frontend facts, missing slot IDs, and stage. All extracted facts require confirmation. SVM scores are decision margins, not probabilities. Unsupported conditional requirements remain explicit in `unresolvedSlots`; readiness does not claim 100% while they exist.

The Home page debounces preview requests and cancels stale requests. Submission creates and analyzes the backend matter before navigation. Understand displays the persisted intent, facts, missing slots, and readiness. The old mock NLP/questioning remains only under explicit `NEXT_PUBLIC_NYAYA_DEMO_MODE=true`; real matters cannot enter prototype legal guidance. Phase 3 now adds adaptive answer capture and persistent verification; see `reports/PHASE3_IMPLEMENTATION.md`. Legal retrieval and generation remain future work.

## Limits and Phase 3 handoff

The baseline poorly covers short, mixed, and unfamiliar utterances; many language and intent outputs abstain. Entity rules do not cover every slot, informal form, negation, or date. Conditional schema rules lack interpretable context and are reported unresolved. AGE is provisional. Real-world, human-reviewed independent evaluation remains necessary. Phase 3 can consume canonical intent, entity, missing-slot, and warning fields to choose schema questions and preserve the same matter ID and revision.
