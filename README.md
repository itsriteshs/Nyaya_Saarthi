# NyayaSaarthi

NyayaSaarthi is a multilingual Motor Vehicle Law research prototype for India. The Next.js frontend has Home, Understand, Verify, Guidance, and Summary pages. The FastAPI backend stores matters in SQLite and runs a dataset-driven NLP baseline for language, intent, entities, normalization, and missing context.

The research flow is **query → lightweight NLP → adaptive clarification → user fact verification → eligibility-filtered hybrid legal retrieval and rule matching → deterministic or locally generated explanation → grounding gate → persisted Summary**. The user verification step confirms the narrative, not the correctness of a legal source. A ranked legal record is never treated by itself as a conclusive legal determination.

## Run the full app locally

Run these macOS/Linux commands from the repository root unless a step says otherwise. For Windows PowerShell paths, see [backend setup](backend/README.md#run-locally). You need Python 3.12 (the tested version), Node.js 20.9 or newer with npm (Node 24 was tested), and [Ollama](https://ollama.com/download) to use the two optional local language models. The first semantic index build downloads a sentence-transformer checkpoint, and the two Ollama pulls download several GB of model weights. Internet access is needed for those first downloads. The app uses SQLite; no separate database server is needed.

### 1. Install dependencies and build the local NLP and legal models (once)

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip install -r backend/requirements-semantic.txt
npm ci
cd backend
.venv/bin/python -m scripts.initialize_database
.venv/bin/python -m scripts.remediation_runtime_artifacts
.venv/bin/python -m scripts.build_legal_index
cd ..
```

`remediation_runtime_artifacts` trains the intent and language classifiers from the grouped training split and writes ignored `backend/artifacts/*.joblib` files. `build_legal_index` creates the hybrid lexical/semantic index under `backend/artifacts/legal_index/`. The first run downloads `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; later builds reuse its saved local checkpoint. If that download is unavailable, run `cd backend && .venv/bin/python -m scripts.build_legal_index --lexical-only` for an explicitly degraded lexical index, then return to the root with `cd ..`. The index must exist for real Guidance, including deterministic guidance. Rebuild it when the legal dataset changes.

### 2. Install both optional explanation models (once)

Start the Ollama app, or run `ollama serve` in a terminal if its service is not already running. In another terminal, run:

```bash
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull mistral:7b-instruct-v0.3-q4_K_M
cd backend
.venv/bin/python -m scripts.check_models
cd ..
```

Both models should appear as available in the check output. Ollama serves them on demand: you do not need a separate `ollama run` process for each model. Keep the Ollama service running while using model explanations. Llama is the default model; the Guidance page lets you choose Llama, Mistral, or deterministic guidance. Downloading Ollama models is optional if you only need deterministic English guidance. See [backend model setup](backend/README.md#phase-5-local-explanations) for model IDs, licences, and limits.

### 3. Launch backend and frontend (each time)

Keep each process running in its own terminal. Start Ollama first if you want Llama or Mistral explanations.

**Terminal A — FastAPI** (from the repository root):

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal B — Next.js** (from the repository root):

```bash
npm run dev
```

Open `http://localhost:3000`. Check `http://127.0.0.1:8000/api/v1/health`, `http://127.0.0.1:8000/api/v1/legal/status`, and `http://127.0.0.1:8000/api/v1/models` if a service or model is unavailable. API docs are at `http://127.0.0.1:8000/docs`. The Home page calls the backend for its NLP preview, creates a matter, and persists analysis before opening Understand. Understand and Verify use backend-managed adaptive questions, answers, fact edits, and verification. Guidance requires a verified matter and the legal index.

### Configuration and checks

The defaults connect the frontend to `http://127.0.0.1:8000`, allow `localhost:3000` through backend CORS, store matters in `backend/nyaya.db`, and connect the backend to Ollama at `http://127.0.0.1:11434`. Copy `.env.example` to `.env.local` in the repository root if you need to change `NEXT_PUBLIC_API_BASE_URL` for Next.js. Restart Next.js after changing a `NEXT_PUBLIC_` variable. Backend settings in `backend/.env.example` are examples of shell variables; FastAPI does not load that file automatically. Export any overrides in the FastAPI terminal before starting it, such as `NYAYA_FRONTEND_ORIGINS` for a different frontend port or `NYAYA_LLM_DEFAULT_MODEL=mistral-7b` to prefer Mistral. Restart FastAPI after changing backend variables. Keep `NEXT_PUBLIC_NYAYA_DEMO_MODE` unset for the real backend flow; setting it to `true` explicitly enables the older frontend mock journey.

From the repository root, run `npm run lint`, `npm run typecheck`, and `npm run build` for frontend checks. From `backend/`, run `.venv/bin/python -m pytest -q` for backend tests. The current setup path is the runtime artifact command above; the older prepare/train/evaluate scripts reproduce historical experiments.

The 23 original datasets remain in `data/Dataset 2/`. Phase 2 methods and evaluation are documented in [backend/PHASE2_IMPLEMENTATION.md](backend/PHASE2_IMPLEMENTATION.md); Phase 3 conversation behavior is documented in [backend/reports/PHASE3_IMPLEMENTATION.md](backend/reports/PHASE3_IMPLEMENTATION.md). Phase 4 legal retrieval and its limits are documented in [backend/reports/PHASE4_IMPLEMENTATION.md](backend/reports/PHASE4_IMPLEMENTATION.md) and [legal knowledge readiness](backend/reports/legal_knowledge_readiness.md).

Phase 5 adds optional local explanations from Llama 3.2 3B Instruct or Mistral 7B Instruct v0.3 using Ollama. The Guidance page shows actual model availability, permits English/Hindi/Hinglish selection, and keeps deterministic guidance available. The Summary page uses the persisted explanation. Install instructions, API contracts, model licences and limitations are in [backend setup](backend/README.md), [Phase 5 report](backend/reports/PHASE5_IMPLEMENTATION.md) and [runtime readiness](backend/reports/model_runtime_readiness.md).

## Phase 6 evaluation and limits

[Phase 6 implementation](backend/reports/PHASE6_IMPLEMENTATION.md) links the measured [NLP](backend/reports/nlp_results.md), [retrieval](backend/reports/retrieval_results.md), [real LLM comparison](backend/reports/llm_comparison.md), [ablations](backend/reports/ablation_study.md), [failure analysis](backend/reports/failure_analysis.md) and [deployment readiness](backend/reports/deployment_readiness.md). Reproducible configurations, split manifests, case-level predictions, metrics and plots are in `backend/experiments/`; runners are in `backend/scripts/phase6_*.py`.

Phase 6 left the original 23 datasets unchanged. The subsequent [quality remediation report](backend/reports/post_phase6_remediation.md) documents two safe CSV/schema repairs, development-only missing-slot improvement, structured-output safeguards and the checks actually completed. Annotation and relevance labels remain pending human review; earlier test examples were exposed to development. The legal index still admits four provisions and no reviewed numeric speed limit, monetary penalty or affirmative procedure. Local matter endpoints have no authentication, so the app is for a trusted local demonstration only. It is not a substitute for professional legal advice or an official decision.
