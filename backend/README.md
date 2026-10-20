# NyayaSaarthi backend

FastAPI stores matters in SQLite and reads the 23 source datasets without changing them. Phase 2 adds locally trained intent and language baselines, rule-based entity extraction, normalization, and intent-specific slot checks. Phase 3 adds persistent adaptive conversation and user verification. Phase 4 adds conservative legal source filtering, rule matching, hybrid retrieval and deterministic guidance.

## Run locally

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/pip install -r backend/requirements-semantic.txt
backend/.venv/bin/python backend/scripts/build_legal_index.py
cd backend
.venv/bin/python -m scripts.initialize_database
.venv/bin/python -m scripts.prepare_nlp_data
.venv/bin/python -m scripts.train_intent_baseline
.venv/bin/python -m scripts.train_language_baseline
.venv/bin/python -m scripts.evaluate_nlp
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger: `http://127.0.0.1:8000/docs`. Tests: `cd backend && .venv/bin/python -m pytest -q`.

## API

All routes use `/api/v1`. Existing health, dataset audit, and matter CRUD routes remain. `POST /nlp/analyze` accepts `{ "text": "I drove my car at 120 km/h in Tamil Nadu", "language": "auto" }`; optional `referenceDatetime` enables relative-date resolution. The response contains language, intent ID and SVM decision score, original-text entity spans, normalized values, missing and unresolved slots, readiness, and warnings. `POST /matters/{id}/analyze` accepts `{ "revision": 1 }`, analyzes the stored original text, and atomically persists the canonical response in `nlpAnalysis` and a frontend display adapter. It accepts DRAFT matters only. Missing local model artifacts return 503; stale revisions return 409.

The baseline needs locally generated `backend/artifacts/*.joblib` files, which are ignored by Git. Only load artifacts you generated or trust: joblib uses Python pickle serialization. Training is never run by an API request.

Phase 3 adds persistent adaptive conversation and verification routes: `GET /matters/{id}/conversation`, `GET /matters/{id}/questions/next`, `POST /matters/{id}/answers`, `PATCH /matters/{id}/facts/{fact_id}`, `POST /matters/{id}/facts/{fact_id}/confirm`, and `POST /matters/{id}/verify`. The answer body contains `revision`, `questionId`, `messageId`, and `answer`; fact and verification operations also require `revision`. See [Phase 3 implementation](reports/PHASE3_IMPLEMENTATION.md). Generic matter PATCH rejects analyzed matters so verification cannot be bypassed.

Phase 4 adds `GET /legal/status`, diagnostic `POST /legal/retrieve` with `{ "matterId": "...", "revision": 1 }`, `POST /matters/{id}/guidance` and `POST /matters/{id}/complete` with `{ "revision": 1 }`. Retrieval and guidance require a persisted user verified matter. A corrected fact invalidates prior guidance. See [Phase 4 implementation](reports/PHASE4_IMPLEMENTATION.md) and [legal knowledge readiness](reports/legal_knowledge_readiness.md). If the embedding model cannot be downloaded, `backend/.venv/bin/python backend/scripts/build_legal_index.py --lexical-only` builds an explicitly degraded lexical index.

## Phase 5 local explanations

Install [Ollama](https://ollama.com/download), start its local service (`ollama serve` if it is not already running), then explicitly download the two selected models:

```bash
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull mistral:7b-instruct-v0.3-q4_K_M
cd backend
.venv/bin/python -m scripts.check_models
```

These tags correspond to `meta-llama/Llama-3.2-3B-Instruct` and `mistralai/Mistral-7B-Instruct-v0.3`; verify and comply with the [Meta Llama community licence](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) and [Mistral Apache-2.0 licence](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3). The Q4_K_M downloads are approximately 2.0 GB and 4.4 GB. Runtime memory also depends on context and concurrent processes. Weights are never downloaded during backend startup or a request. The default is Llama; set `NYAYA_LLM_DEFAULT_MODEL=mistral-7b` to change it. Other options and defaults are in `.env.example`. Only localhost Ollama URLs are accepted. The deterministic path works with neither model installed.

`GET /api/v1/models` and `/models/health` report actual local readiness. `POST /api/v1/matters/{id}/generate` takes `modelId` (`llama3.2-3b`, `mistral-7b`, or `deterministic`), `language` (`english`, `hindi`, `hinglish`), `expectedRevision`, and optional `regenerate: true`. It returns the updated persisted matter. To try both installed models with one frozen verified matter without changing it: `.venv/bin/python -m scripts.run_llm_smoke MATTER_UUID --language hindi`. This script prints metadata only. See [Phase 5 implementation](reports/PHASE5_IMPLEMENTATION.md) for the earlier implementation state and [Phase 6 comparison](reports/llm_comparison.md) for actual local inference results.

## Reproduce Phase 6 locally

Use the setup commands above, then run these commands from `backend/`. The original dataset audit exits nonzero while the two documented source-data errors remain; its report is still generated. The derived overlay is for research review only. The Phase 6 runners write to `experiments/`, so move or archive existing results before rerunning if you need to preserve them.

Install the plotting dependency with `.venv/bin/pip install -r requirements-evaluation.txt` from `backend/`.

```bash
.venv/bin/python -m scripts.validate_datasets
.venv/bin/python -m scripts.phase6_dataset_overlay /tmp/nyaya_phase6_dataset_overlay
.venv/bin/python -m scripts.phase6_data_audit
.venv/bin/python -m scripts.phase6_nlp_experiment
.venv/bin/python -m scripts.build_legal_index
.venv/bin/python -m scripts.phase6_retrieval_eval
.venv/bin/python -m scripts.phase6_freeze_cases
.venv/bin/python -m scripts.phase6_llm_compare --model llama3.2-3b
ollama stop llama3.2:3b-instruct-q4_K_M
.venv/bin/python -m scripts.phase6_llm_compare --model mistral-7b
.venv/bin/python -m scripts.phase6_ablations
.venv/bin/python scripts/phase6_plots.py
.venv/bin/python scripts/phase6_write_reports.py
.venv/bin/python -m pytest tests -q
```

For an isolated HTTP demonstration, start FastAPI with a temporary database and the matching frontend CORS origin, then use `NEXT_PUBLIC_API_BASE_URL` for the Next.js process:

```bash
NYAYA_DATABASE_URL=sqlite:////tmp/nyaya_phase6_demo.db NYAYA_FRONTEND_ORIGINS=http://127.0.0.1:3010 .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010 npm run dev -- --hostname 127.0.0.1 --port 3010
.venv/bin/python -m scripts.phase6_e2e_smoke --base-url http://127.0.0.1:8010 --model deterministic
```

Run the Next.js command from the repository root and the other commands from `backend/`. The SQLite file stores test matters; do not expose the unauthenticated API publicly. See [Phase 6 deployment readiness](reports/deployment_readiness.md) for the tested environment and limits.

## Configuration and limits

`NYAYA_DATABASE_URL` defaults to `backend/nyaya.db`. `NYAYA_DATASET_DIR` and `NYAYA_REPORT_DIR` override dataset and report locations. `NYAYA_FRONTEND_ORIGINS` is a comma-separated CORS allowlist. The frontend uses `NEXT_PUBLIC_API_BASE_URL`. The API is for local development and has no authentication. The dataset audit remains an explicit offline command: `.venv/bin/python -m scripts.validate_datasets`.

See [PHASE2_IMPLEMENTATION.md](PHASE2_IMPLEMENTATION.md), [dataset readiness](reports/nlp_dataset_readiness.md), and [evaluation](reports/nlp_evaluation.md). Annotation labels and legal sources have limited human review. The application does not independently authenticate linked government pages.
