# NyayaSaarthi backend

FastAPI stores matters in SQLite and reads the 23 source datasets without changing them. Phase 2 adds locally trained intent and language baselines, rule-based entity extraction, normalization, and intent-specific slot checks. Phase 3 adds persistent adaptive conversation and user verification. It does not determine legal applicability.

## Run locally

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
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

## Configuration and limits

`NYAYA_DATABASE_URL` defaults to `backend/nyaya.db`. `NYAYA_DATASET_DIR` and `NYAYA_REPORT_DIR` override dataset and report locations. `NYAYA_FRONTEND_ORIGINS` is a comma-separated CORS allowlist. The frontend uses `NEXT_PUBLIC_API_BASE_URL`. The API is for local development and has no authentication. The dataset audit remains an explicit offline command: `.venv/bin/python -m scripts.validate_datasets`.

See [PHASE2_IMPLEMENTATION.md](PHASE2_IMPLEMENTATION.md), [dataset readiness](reports/nlp_dataset_readiness.md), and [evaluation](reports/nlp_evaluation.md). Annotation labels and legal sources are pending human review. Legal retrieval and legal guidance are outside Phase 2.
