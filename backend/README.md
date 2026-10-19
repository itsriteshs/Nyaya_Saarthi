# NyayaSaarthi Phase 1 backend

FastAPI stores user matters in SQLite. The 23 research datasets remain read-only files in `../data/Dataset 2/`; the dataset audit is an explicit offline command. This backend does not implement NLP, legal retrieval, or legal advice.

## Setup and run

Python 3.11+ is required. From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cd backend
.venv/bin/python -m scripts.initialize_database
.venv/bin/python -m scripts.validate_datasets
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Swagger is at `http://127.0.0.1:8000/docs`. Run tests from the root with `backend/.venv/bin/python -m pytest backend/tests -q`.

`NYAYA_DATABASE_URL` defaults to a SQLite file at `backend/nyaya.db`. `NYAYA_DATASET_DIR` and `NYAYA_REPORT_DIR` may override the repository-relative paths. `NYAYA_FRONTEND_ORIGINS` is a comma-separated allowlist, defaulting to localhost and 127.0.0.1 on port 3000. Copy `.env.example` values into your shell environment as needed; no secrets belong in `NEXT_PUBLIC_*` variables. SQLite files are ignored by Git.

## API

All paths use `/api/v1`:

| Method | Path | Meaning |
|---|---|---|
| GET | `/health` | Process health only |
| GET | `/datasets/summary` | Cached file metadata |
| GET | `/datasets/validation` | Last completed audit, or `not_run` |
| POST | `/matters` | Create a DRAFT matter from `originalText` and `language`; returns 201 |
| GET | `/matters/{id}` | Retrieve, or 404 |
| PATCH | `/matters/{id}` | Partial update with required `revision`; returns 409 for stale revision |
| DELETE | `/matters/{id}` | Delete; returns 204 or 404 |

PATCH accepts only documented context fields. Lists and objects replace their whole field; omitted fields stay unchanged; explicit `null` removes an optional field. `id`, `originalText`, and `language` are immutable. Every accepted update increments `revision`. The server retains `schemaVersion=1` for future migrations. Malformed bodies return 422; bodies over 256 KB return 413. Future schema changes require an explicit versioned migration before deployment.

The current reviewed audit has 2 genuine errors and 341 warnings; see `reports/PHASE1_VERIFICATION.md`, `PHASE1_REFERENCE_INVENTORY.csv`, and `PHASE1_PROPOSED_DATASET_CHANGES.md`. Run `.venv/bin/python -m scripts.reference_inventory` after each audit to refresh the reference inventory. The validator exits 1 for `ERROR` issues (malformed records, invalid IDs, or required broken links). `WARNING` and `INFO` do not make it fail. The run writes `reports/dataset_audit.json` and `.md` even if it exits 1. No HTTP request launches the full audit. A report is a diagnostic inventory; row review status does not independently establish legal correctness.

## Integration and limits

The typed frontend client lives in `src/lib/api/`. The current five-page journey still uses `sessionStorage` and mock helpers. In Phase 2, the NLP service can populate the persisted matter's `intent`, `facts`, `missingSlots`, and `contextReadiness` after creation; its frontend replacement point is `createMatterContext`/`analyzeSituation`. Phase 3 can replace `answerCurrentQuestion`; Phase 4 can replace `mockLegalRetrieval`. These are interfaces to implement later, not endpoints in this phase.

The API is unauthenticated and intended only for controlled local development. Anyone who can reach it can access matters by ID. No legal datasets are imported into SQLite. No source URLs are checked live. Review dates are not interpreted as proof of current legal effect. The current API does not synchronize the existing frontend session.
