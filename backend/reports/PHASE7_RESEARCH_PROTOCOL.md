# Explainability and Phase 7 research protocol

## Scope and safety
Research is available at /research from Home and the shared footer. The original five-step workflow remains. Read-only endpoints: /api/v1/research/catalog, /research/runs/{run_id}, /research/matters/{matter_id}/trace. They do not perform inference, retrieval, evaluation or downloads. They share the existing local matter-ID access model, not multi-user authorization.

No legal dataset, grounding rule, generator model or user verification requirement changes. The deterministic extractor is invoked only for offline ablation.

## Trace semantics
Future analyses record TF-IDF input, fitted LinearSVC signed n-gram contributions (value times coefficient), intercept, complete contribution sum, margins, top three classes and model SHA256. Sum plus intercept reconstructs the decision score. Overlapping character features are not causal evidence or probabilities. Old attributions remain unavailable. Original prediction and user-selected workflow are separate.

Language shows recorded requested/detected language, classifier/script evidence and uncertainty. Facts retain source spans, normalization, provenance and confirmation. SLM interpretation is not user confirmation. Only current question rationale is guaranteed stored; messages cannot reconstruct historical planner rationales. Retrieval shows saved rank, BM25 and semantic scores, exclusions, rules and mappings. Claim strings link to recorded evidence IDs/source URLs. Missing sentence links are not inferred.

No NLI evaluator is configured. Default local cache contains NER/GPT2; project has a multilingual sentence embedding model. None is an identified licensed NLI checkpoint. No weights downloaded. Semantic entailment is unavailable, not zero. A future opt-in NLI adapter needs a local checkpoint, revision/hash, license, class mapping, development threshold selection and reserved evaluation. Its scores remain screening proxies, never legal truth.

## Commands (PowerShell, repository root)
Each unique run ID creates a new directory and refuses overwrite. No writes to historical reports or grouped-test predictions.

    $env:PYTHONPATH="$PWD/backend"
    $env:HF_HUB_OFFLINE="1"
    $env:TRANSFORMERS_OFFLINE="1"
    .venv/Scripts/python.exe -X utf8 -m scripts.phase7_research --run-id dev-UNIQUE --nlp --probe
    .venv/Scripts/python.exe -X utf8 -m scripts.phase7_retrieval_context --run-id retrieval-context-dev-UNIQUE
    .venv/Scripts/python.exe -X utf8 -m scripts.phase7_generation --run-id generation-dev-UNIQUE --languages english hindi hinglish
    .venv/Scripts/python.exe -X utf8 -m scripts.phase7_slm_compare --run-id extraction-dev-UNIQUE --cases reviewed-development.json --model llama3.2-3b

Generation is opt-in and requires local Ollama with llama3.2:3b-instruct-q4_K_M and mistral:7b-instruct-v0.3-q4_K_M. Same frozen evidence, languages, temperature 0, seed 471, context 8192 and configured token/timeout limits. One trial per cell; cold starts affect timing. Runtime, timeout, truncation, schema, language and grounding failures are retained. Conditional schema/grounding/language rates have explicit denominators; overall acceptance/fallback include all model attempts. Raw outputs and token counts are retained. Deterministic comparison uses frozen English Guidance, not new translation; its different schema and unrecorded latency are explicit.

## Classification and extraction
Only train/dev rows from phase6_grouped_split.csv enter the experiment. No grouped-test evaluation. Controlled SVC and logistic regression use identical train rows, character TF-IDF (3–5, min_df 2, max_features 100000), seed 471. Production SVC is separate because it includes ontology examples. No production model files overwritten. Language models, policy and thresholds were already developed on these data.

Accuracy=correct/N. Macro-F1=unweighted class F1. Precision=TP/(TP+FP); recall=TP/(TP+FN); F1=2TP/(2TP+FP+FN). Undefined denominator=null. Confusion matrices retain label order. Language coverage excludes mixed/uncertain abstentions; overall accuracy counts abstentions wrong. Entity span equality uses slot+start+end; slot-presence ignores values. Reviewed normalization gold is absent. Wilson 95% intervals and paired bootstrap (1000 case resamples, seed 471) describe sampling only; templates/annotation errors can make them optimistic.

## Reviewed extraction input
JSON requires split=development, reviewStatus=REVIEWED, reviewer=<actual human>, cases=[...]. Case: unique id, text, intentId, timezone-aware referenceDatetime, entities. Entity: slot, quote, start, end, normalizedValue, optional status. Quote must match offsets. Labels must be exhaustive. Never mark agent-created labels reviewed without human review. Pending/test inputs are rejected.

The same cases/timestamps go through deterministic normalization and actual SLM interpret. Reports slot+value and span PRF, unresolved counts, latency, failure, unsupported-label disagreement and redundant-missing-question proxy with gold intent. SLM-only failures have no fallback; zero fallback is policy, not success. No reviewed input supplied, so no SLM superiority is claimed. App-generated full conversation outcomes remain unavailable.

## Retrieval and adaptive context
Ranking selects only query IDs assigned dev in the manifest and loads the existing index offline. BM25, semantic and RRF(k=60) rank identical cases/corpus. Recall@k=mean fraction of admitted positives retrieved; MRR=mean first-positive reciprocal rank. Excluded-only positives are counted separately. Unjudged precision unavailable. Recall@5 has little discrimination with four provisions. Development queries were exposed historically: no independent performance claim.

Adaptive selects source conversations with split=validation (the dataset development partition; dev is also accepted). Compares initial/final recorded unconditional required-slot coverage, recorded questions/redundancy against accumulated slots, completion among conversations with requirements. This is a recorded-data proxy. Conditional requirements and current generated outcomes are not scored.

## Adversarial faithfulness
probe_cases.json has human-reviewable development/reserved_probe pairs for eight corruption types. Fictional administrative source cards are not legal dataset records. Labels are agent-authored, PENDING review. Desk identifiers differ across groups, but templates overlap; no independent benchmark.

Pre-existing Boolean gate is frozen. No threshold tuned on either group. Disabled comparator accepts all offline only. Detection=flagged corrupt/corrupt; false positives=flagged clean/clean, per type. Repeated clean examples cannot be aggregated as independent. Semantic misses remain visible. This is not a production hallucination rate or NLI score.

## Historical results and gaps
Exact Phase 6 JSONs are read unchanged. They remain exploratory: exposed grouped test, pending annotations, different case sets, recorded conversation proxy, three-case rule exposure proxy, nine generations/model, no semantic/human ratings. No overall score.

Still needed: reviewed SLM/normalization examples; generated conversation comparison; reviewed applicability labels; licensed local NLI and reviewed pairs; blinded multilingual clarity/usefulness/faithfulness ratings; untouched independent evaluation data.

## Source reproducibility
The runners now capture source_snapshot.zip (backend app/scripts only), environment.json with dependency versions, commands and model hashes at run start. No private matter database is included. Initial runs made during implementation predate this addition; their recorded model/split/config fingerprints and case predictions are preserved, and this limitation is explicit. Use a new run ID to capture a complete source snapshot for subsequent experiments.

## Checks
    .venv/Scripts/python.exe -X utf8 -m pytest backend/tests -q
    npm run lint
    npm run typecheck
    npm run build

Browser runner: backend/scripts/research_browser.mjs, using Playwright and local Chrome. Serve an isolated backend at 8002 and production frontend at 3002. Set PLAYWRIGHT_MODULE to the installed Playwright module if it is not on Node's resolution path. Optional RESEARCH_TEST_MATTER_ID selects a saved matter; otherwise the script creates and deletes a draft fixture. It checks traces, errors, missing artifacts, per-type results and 360px document overflow. Screenshots/check results live in experiments/phase7/browser-check. These UI fixtures are not evaluation cases.
