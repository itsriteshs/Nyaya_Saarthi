# NyayaSaarthi

NyayaSaarthi is a multilingual Motor Vehicle Law research prototype for India. The Next.js frontend has Home, Understand, Verify, Guidance, and Summary pages. The FastAPI backend stores matters in SQLite and runs a dataset-driven NLP baseline for language, intent, entities, normalization, and missing context.

The research flow is **query → lightweight NLP → adaptive clarification → user fact verification → eligibility-filtered hybrid legal retrieval and rule matching → deterministic or locally generated explanation → grounding gate → persisted Summary**. The user verification step confirms the narrative, not the correctness of a legal source. A ranked legal record is never treated by itself as a conclusive legal determination.

## Run locally

Set up and train the backend as described in [backend/README.md](backend/README.md), then start its FastAPI server. In another terminal:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`. The Home page calls the backend for its NLP preview, creates a matter, and persists analysis before opening Understand. Understand and Verify use backend-managed adaptive questions, answers, fact edits, and verification. Set `NEXT_PUBLIC_API_BASE_URL` if FastAPI is not at `http://127.0.0.1:8000`. `NEXT_PUBLIC_NYAYA_DEMO_MODE=true` explicitly enables the older frontend mock journey for development; real mode never silently falls back to mock NLP.

The 23 original datasets remain in `data/Dataset 2/`. Phase 2 methods and evaluation are documented in [backend/PHASE2_IMPLEMENTATION.md](backend/PHASE2_IMPLEMENTATION.md); Phase 3 conversation behavior is documented in [backend/reports/PHASE3_IMPLEMENTATION.md](backend/reports/PHASE3_IMPLEMENTATION.md). Phase 4 legal retrieval and its limits are documented in [backend/reports/PHASE4_IMPLEMENTATION.md](backend/reports/PHASE4_IMPLEMENTATION.md) and [legal knowledge readiness](backend/reports/legal_knowledge_readiness.md). Build the legal index using the commands in the backend README before opening real Guidance. Frontend checks: `npm run lint`, `npm run typecheck`, `npm run build`.

Phase 5 adds optional local explanations from Llama 3.2 3B Instruct or Mistral 7B Instruct v0.3 using Ollama. The Guidance page shows actual model availability, permits English/Hindi/Hinglish selection, and keeps deterministic guidance available. The Summary page uses the persisted explanation. Install instructions, API contracts, model licences and limitations are in [backend setup](backend/README.md), [Phase 5 report](backend/reports/PHASE5_IMPLEMENTATION.md) and [runtime readiness](backend/reports/model_runtime_readiness.md).

## Phase 6 evaluation and limits

[Phase 6 implementation](backend/reports/PHASE6_IMPLEMENTATION.md) links the measured [NLP](backend/reports/nlp_results.md), [retrieval](backend/reports/retrieval_results.md), [real LLM comparison](backend/reports/llm_comparison.md), [ablations](backend/reports/ablation_study.md), [failure analysis](backend/reports/failure_analysis.md) and [deployment readiness](backend/reports/deployment_readiness.md). Reproducible configurations, split manifests, case-level predictions, metrics and plots are in `backend/experiments/`; runners are in `backend/scripts/phase6_*.py`.

The original 23 datasets are unchanged. Annotation and relevance labels are pending human review; earlier test examples were exposed to development. The legal index admits four provisions and no reviewed numeric speed limit, monetary penalty or affirmative procedure. Local matter endpoints have no authentication, so the app is for a trusted local demonstration only. It is not a substitute for professional legal advice or an official decision.
