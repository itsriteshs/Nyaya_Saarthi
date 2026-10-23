# Phase 7 implementation and evidence report

Implemented the expanded research workflow without changing the five citizen routes, legal datasets, production generator models, or safety gates. This is a development research implementation, not a completed independent legal evaluation.

## Implementation audit

Initial regression state: 142 backend tests passed. Existing /research, stored SVM feature attribution, historical comparisons and development runners were reused. Missing features included Naive Bayes, measured local surrogate explanations, a sectioned console, controlled R0–R3 runner and publication exports. Current intake genuinely invokes the local SLM; older documentation describing rule-first intake was stale. Deterministic extraction remains an offline baseline, not production intake fallback.

## Implemented

- Eleven-section Evaluation console on /research; existing Matter explainability and Ablation studies views preserved.
- Dataset inventory/statistics, template leakage indicators, current eligibility and fresh read-only reference audit.
- Controlled character TF-IDF SVC, logistic regression and Multinomial Naive Bayes on identical train/dev rows. Added training/inference times, serialized artifact sizes, per-class/macro/weighted scores and case predictions.
- Language policy diagnostics, per-language intent/entity/missing-slot diagnostics, exact and relaxed one-to-one entity span matching.
- LIME-style token-deletion weighted Ridge explanations of actual SVM margins: 300/600 perturbations, three seeds, 100 separate perturbations for held-out surrogate scoring. This is a transparent implementation, not the lime package.
- BM25/semantic/equal RRF plus fixed 25%/75% lexical-weight sensitivity. No production setting selected or changed.
- Offline R0 bare-context / R1 evidence / R2 rule-and-validator / R3 frozen deterministic pilot. Unvalidated outputs are research artifacts only.
- JUnit import with case-level assertions, sanitized NLP example records, language/model/case selectors, export selection, downloadable publication files.
- PNG/SVG/PDF publication plots, CSV tables, captions, source reports and implemented architecture/pseudocode.

## Actual measurements

| Component | Cases | Measurement | Status |
|---|---:|---|---|
| Intent SVC | 1,156 dev | accuracy 1.000, macro-F1 1.000 | synthetic, unreviewed development |
| Intent logistic regression | same 1,156 | accuracy 1.000, macro-F1 1.000 | same split/features |
| Intent Naive Bayes | same 1,156 | accuracy 0.993945, macro-F1 0.992173 | seven errors |
| Entity deterministic baseline | same 1,156 | strict one-to-one exact F1 0.843797; relaxed IoU>=0.5 F1 0.848193 | offline baseline, not SLM quality |
| Retrieval | 113 answerable / 211 total dev queries | R@1 BM25 0.6460, semantic 0.6814, hybrid 0.8673 | four eligible provisions; labels pending |
| Weighted fusion | same queries | lexical25 R@1 0.6814; lexical75 0.7699 | fixed sensitivity, no production tuning |
| Recorded adaptive context | 450 validation conversations / 1,350 required observations | coverage 0.3281 to 0.8030; mean questions 1.5911 | recorded-data proxy |
| Local surrogate explanations | six selected dev examples / 36 explanations | mean held-out R2 0.98460, top-five 300-perturbation stability 0.96296 | local explanation fidelity, not correctness |
| Existing English frozen generation run | three packages per model | Llama 1/3 accepted; Mistral 0/3 | two Llama truncations, three Mistral timeouts |
| New RAG pilot | one frozen case x two models x three generated conditions | Llama R0/R2 truncated, R1 parsed but gate rejected; all Mistral cells timeout | no quality superiority claim |
| Dataset reference validation | 23 files / 20,214 rows | one critical error, 341 warnings | no source repairs or legal review |
| Final backend suite | 148 tests | 148 passed | fixture/API/component tests, not human acceptance |

Perfect SVC/LR results are consistent with templated data and already-exposed development material; they do not establish real-world performance. No grouped-test experiments were rerun. Earlier set-based span metrics collapse duplicate predictions; the new one-to-one span diagnostic counts duplicate predictions as false positives and is labeled separately. Timings were collected locally during other research activity, with cold model loads; they are not an isolated hardware comparison.

## Experiments and reproducibility

PowerShell from repository root; set PYTHONPATH to the backend folder first. All new run IDs refuse overwrite. Historical Phase 6 artifacts remain unchanged. Source snapshots/dependency/model fingerprints are captured by the runners.

Executed component commands (each via .venv/Scripts/python.exe -X utf8):

    -m scripts.phase7_research --run-id three-model-dev-20261023 --nlp --probe
    -m scripts.phase7_advanced --run-id advanced-dev-20261023 --audit --lime
    -m scripts.phase7_advanced --run-id audit-final-dev-20261023 --audit
    -m scripts.phase7_rag --run-id rag-pilot-dev-20261023 --limit 1
    -m scripts.phase7_retrieval_context --run-id fusion-dev-20261023
    -m scripts.phase7_entity_diagnostic --run-id entity-dev-20261023 --source-run three-model-dev-20261023
    -m pytest backend/tests -q --junitxml=backend/experiments/phase7/reliability-complete-20261023.xml
    -m scripts.phase7_test_report --source backend/experiments/phase7/reliability-complete-20261023.xml --run-id reliability-complete-dev-20261023
    -m scripts.phase7_architecture

Export command: -m scripts.phase7_export --run-id RUN_ID. Executed for advanced-dev-20261023, three-model-dev-20261023, retrieval-context-dev-20261023-v3, fusion-dev-20261023, generation-dev-20261023-v1, rag-pilot-dev-20261023. Install optional plotting dependency with pip install -r backend/requirements-research.txt. No weights are downloaded by the app.

Available aggregate workflow: -m scripts.phase7_all --prefix UNIQUE, optionally --local-models. The wrapper itself was not rerun because its component jobs were already executed individually. Reviewed SLM comparisons remain available through phase7_slm_compare with actual human-reviewed development inputs.

Frontend checks executed using the installed Node runtime: node node_modules/typescript/bin/tsc --noEmit; node node_modules/eslint/bin/eslint.js .; node node_modules/next/dist/bin/next build. These correspond to npm run typecheck, lint and build. Browser command: node backend/scripts/research_browser.mjs with installed Playwright; isolated API port 8002 and production Next port 3002. Browser assertions cover saved matter traces, errors, empty artifacts, development selection, per-type tables, console navigation, Naive Bayes filtering, LIME section, and 360px document overflow. Screenshots inspected. Existing five-page routes build; no fresh full native PDF/user-acceptance pass is claimed.

## API and UI

New read-only endpoints: /api/v1/research/runs/{id}/examples; /runs/{id}/exports; /runs/{id}/exports/{filename}. Existing catalog, run and matter-trace APIs retained. No model inference/evaluation runs on page load. Matter trace highlights only matching recorded offsets; SLM extraction and user confirmation remain separate. Local endpoints retain the existing trusted-local access assumption.

## Status and remaining limits

FIXED: missing classifier baseline, measured local surrogate explanation, section navigation, stored example filters, reproducible plots/tables, export API, and accessible experiment selector. Evidence is in versioned metrics/predictions and passing browser/backend checks.

PARTIALLY FIXED: RAG/LLM benchmarking is an actual small English pilot with runtime failures, not a completed multilingual/scenario study. Dataset auditing identifies defects but intentionally leaves legal data unchanged. Research export covers measured experiments; not every requested figure/table exists. Three conditions share the same structural prompt; the bare condition is evidence-free, not unconstrained chat.

BLOCKED BY DATA/REVIEW: no reviewed SLM/normalization comparison set; no qualified claim-support/applicability/hallucination labels; no blinded human ratings; no configured licensed NLI; no untouched independent benchmark. Current recorded conversations cannot establish a causal benefit of adaptive versus fixed questioning.

NOT VERIFIED / NOT IMPLEMENTED AS A NEW STUDY: full citizen five-page browser acceptance and native PDF save; live controlled fixed/adaptive policy comparison; complete multilingual RAG scenario suite; paired multilingual semantic-equivalence gold; calibrated reliability diagram; all requested latency/memory/figure families. These are not silently represented as zero or passing.

Team-selected baseline paper and fair comparison: PHASE7_BASELINE_PAPER.md. Implemented algorithms and publication placement: PHASE7_ALGORITHMS.md. Broader protocol and safety definitions: PHASE7_RESEARCH_PROTOCOL.md.

## Modified implementation files

- backend/app/api/research.py
- backend/app/services/research/lime.py
- backend/app/services/research/metrics.py
- backend/app/services/research/protocol.py
- backend/reports/PHASE7_ALGORITHMS.md
- backend/reports/PHASE7_BASELINE_PAPER.md
- backend/requirements-research.txt
- backend/scripts/phase7_advanced.py
- backend/scripts/phase7_all.py
- backend/scripts/phase7_architecture.py
- backend/scripts/phase7_entity_diagnostic.py
- backend/scripts/phase7_export.py
- backend/scripts/phase7_rag.py
- backend/scripts/phase7_research.py
- backend/scripts/phase7_retrieval_context.py
- backend/scripts/phase7_test_report.py
- backend/scripts/research_browser.mjs
- backend/tests/test_phase7_advanced.py
- src/components/research/AdvancedConsole.tsx
- src/components/research/ResearchDashboard.tsx

## Exact publication figure inventory

- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_language.png; SVG/PDF alongside. Aggregate synthetic corpus audit; N=10000; annotation review pending.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_intent.png; SVG/PDF alongside. Aggregate synthetic corpus audit; N=10000; annotation review pending.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_entities.png; SVG/PDF alongside. Aggregate synthetic corpus audit; N=10000; annotation review pending.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_partitions.png; SVG/PDF alongside. Aggregate synthetic corpus audit; N=10000; annotation review pending.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_records.png; SVG/PDF alongside. Source file record counts; see TABLE I for file hashes.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_lengths.png; SVG/PDF alongside. Whitespace length distribution, N=10000.
- backend\experiments\phase7\advanced-dev-20261023\publication\DATA_missing.png; SVG/PDF alongside. Mean missing-field percentages by source file; full field counts in metrics JSON.
- backend\experiments\phase7\advanced-dev-20261023\publication\XAI_02_fidelity.png; SVG/PDF alongside. LIME-style weighted Ridge; 6 selected synthetic development cases.
- backend\experiments\phase7\advanced-dev-20261023\publication\XAI_03_stability.png; SVG/PDF alongside. Top-five position Jaccard over three seeds, 300 perturbations.
- backend\experiments\phase7\advanced-dev-20261023\publication\XAI_01_tokens.png; SVG/PDF alongside. Token contributions to SVM margin surrogate; not probabilities or legal evidence.
- backend\experiments\phase7\fusion-dev-20261023\publication\RET_recallat1.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\fusion-dev-20261023\publication\RET_recallat3.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\fusion-dev-20261023\publication\RET_mrr.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\fusion-dev-20261023\publication\CONV_coverage.png; SVG/PDF alongside. Recorded development-data proxy, N=450; not generated app comparison.
- backend\experiments\phase7\generation-dev-20261023-v1\publication\LLM_acceptance.png; SVG/PDF alongside. Three English synthetic development packages per model; structural proxy only.
- backend\experiments\phase7\rag-pilot-dev-20261023\publication\RAG_schema.png; SVG/PDF alongside. One frozen English development case per model/condition. Schema proxy, not legal support.
- backend\experiments\phase7\retrieval-context-dev-20261023-v3\publication\RET_recallat1.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\retrieval-context-dev-20261023-v3\publication\RET_recallat3.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\retrieval-context-dev-20261023-v3\publication\RET_mrr.png; SVG/PDF alongside. Identical development queries and eligible corpus; label review pending.
- backend\experiments\phase7\retrieval-context-dev-20261023-v3\publication\CONV_coverage.png; SVG/PDF alongside. Recorded development-data proxy, N=450; not generated app comparison.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_01_accuracy.png; SVG/PDF alongside. Same 1156 development cases; unreviewed labels; metric=accuracy.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_04_training.png; SVG/PDF alongside. Same 1156 development cases; unreviewed labels; metric=trainingMs.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_05_latency.png; SVG/PDF alongside. Same 1156 development cases; unreviewed labels; metric=meanInferenceMs.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_02_linear_svc.png; SVG/PDF alongside. Confusion matrix N=1156; class order in metrics JSON; development only.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_02_logistic_regression.png; SVG/PDF alongside. Confusion matrix N=1156; class order in metrics JSON; development only.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_02_multinomial_nb.png; SVG/PDF alongside. Confusion matrix N=1156; class order in metrics JSON; development only.
- backend\experiments\phase7\three-model-dev-20261023\publication\INT_02_production_svc.png; SVG/PDF alongside. Confusion matrix N=1156; class order in metrics JSON; development only.
- backend\experiments\phase7\three-model-dev-20261023\publication\NLP_language_intent.png; SVG/PDF alongside. Intent accuracy by annotated language; denominators in metrics JSON.
- backend\experiments\phase7\architecture-20261023\architecture.png; SVG/PDF alongside. Actual implemented layers, no metric claim.
