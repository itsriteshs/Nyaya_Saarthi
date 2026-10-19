# NyayaSaarthi

NyayaSaarthi is a multilingual Motor Vehicle Law assistant prototype for India. The Next.js frontend has five pages: Home (`/`), Understand (`/understand`), Verify (`/verify`), Guidance (`/guidance`), and Summary (`/summary`). They currently use local mock NLP, questioning, and legal retrieval with `sessionStorage` for the journey. Phase 1 adds a separate FastAPI backend for dataset auditing and persistent matters, without changing the UI flow.

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`. Run frontend checks with `npm run lint`, `npm run typecheck`, and `npm run build`.

For backend setup, audit, API endpoints, and tests, see [backend/README.md](backend/README.md). The backend runs at `http://127.0.0.1:8000` and its Swagger docs are at `/docs`. The frontend API client uses `NEXT_PUBLIC_API_BASE_URL` (see `.env.example`), but the UI still uses the mock session flow until later phases.

The original 23 CSV/JSONL datasets are preserved in `data/Dataset 2/`; see [Phase 1 findings](backend/reports/PHASE1_DATASET_FINDINGS.md). The older static HTML prototypes remain at the repository root. `NLP_FLOW.pdf`, `NLP_CONCEPTS.pdf`, and `Team_18 (1).pptx` remain historical product source material where available.
