# Phase 6 NLP results

The source annotation set has 10,000 utterances (original train/dev/test: 8,000/1,000/1,000). Original splits share 124 normalized texts and 175 digit-masked template families. The derived connected scenario/template manifest has train/dev/test **4,634/1,156/1,444** and excludes 2,766 rows overlapping gold templates; zero connected groups cross derived partitions. The original test was exposed in prior development, and all labels are pending review. These are exploratory scores, not an independent benchmark.

| Task | Grouped test result | Notes |
|---|---:|---|
| Intent accuracy / macro F1 | 100.0% / 100.0% | Character SVM chosen on development; word logistic regression also scored 100% on development. Template cues make this an optimistic result. |
| Language coverage / accuracy on answered / overall accuracy | 90.3% / 100.0% / 90.3% | Abstentions count as wrong overall. |
| Prior mixed-script policy overall, same grouped split | 60.2% | Phase 6 Devanagari-dominance policy replaces treating any mixed script as `mixed`. |
| Entity exact-span precision / recall / F1 | 92.7% / 92.9% / 92.8% | TP 3008, FP 237, FN 230; original offsets. |
| Missing-slot precision / recall / F1 | 16.8% / 84.9% / 28.0% | TP 316, FP 1570, FN 56. |
| Missing-slot exact set | 17.9% | Oracle intent gives the same F1; intent errors are not the driver on this split. |

The main unresolved defect is missing-slot precision: many policy-required `USER_ROLE` and `VEHICLE_CLASS` slots are absent from recorded missing-slot labels. We retained the requirements and report the mismatch. A training-fold-only status phrase vocabulary prevents annotation values in test from entering entity inference. Full per-intent, per-language, per-entity and confusion matrices are in `experiments/metrics/phase6_nlp.json`; case-level predictions are in `experiments/predictions/phase6_nlp.jsonl`. Figures: `experiments/plots/language_policy.png` and `language_confusion.png`.
