# NyayaSaarthi

NyayaSaarthi is a multilingual Motor Vehicle Law research prototype for India. The Next.js frontend has Home, Understand, Verify, Guidance, and Summary pages. The FastAPI backend stores matters in SQLite and runs a dataset-driven NLP baseline for language, intent, entities, normalization, and missing context.

## Run locally

Set up and train the backend as described in [backend/README.md](backend/README.md), then start its FastAPI server. In another terminal:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`. The Home page calls the backend for its NLP preview, creates a matter, and persists analysis before opening Understand. Understand and Verify use backend-managed adaptive questions, answers, fact edits, and verification. Set `NEXT_PUBLIC_API_BASE_URL` if FastAPI is not at `http://127.0.0.1:8000`. `NEXT_PUBLIC_NYAYA_DEMO_MODE=true` explicitly enables the older frontend mock journey for development; real mode never silently falls back to mock NLP.

The 23 original datasets remain in `data/Dataset 2/`. Phase 2 methods and evaluation are documented in [backend/PHASE2_IMPLEMENTATION.md](backend/PHASE2_IMPLEMENTATION.md); Phase 3 conversation behavior is documented in [backend/reports/PHASE3_IMPLEMENTATION.md](backend/reports/PHASE3_IMPLEMENTATION.md). Phase 4 legal retrieval and its limits are documented in [backend/reports/PHASE4_IMPLEMENTATION.md](backend/reports/PHASE4_IMPLEMENTATION.md) and [legal knowledge readiness](backend/reports/legal_knowledge_readiness.md). Build the legal index using the commands in the backend README before opening real Guidance. Frontend checks: `npm run lint`, `npm run typecheck`, `npm run build`.
