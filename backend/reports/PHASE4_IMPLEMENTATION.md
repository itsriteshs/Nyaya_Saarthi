# Phase 4 implementation

## Components and data model

`app/services/legal/knowledge.py` loads legal sources, provisions, rules, offences, speed limits, procedures, steps, documents, forms, services, accident relief, case law, explanations, coverage, jurisdictions, vehicles and intents from the unchanged Dataset 2 files. Each loaded row retains its source filename and physical row. Malformed records are excluded with a reason. A SHA-256 fingerprint covers all loaded files.

`policy.py` classifies source and provision records as eligible, conditional or excluded. Eligibility requires local `VERIFIED` review metadata, a primary source, HTTPS URL on an allowlisted government host, source review date, full commencement, an active provision, and a valid jurisdiction. Retrieval additionally requires an event date and jurisdiction; central law can apply within a known Indian jurisdiction. Effective date bounds are checked at event time. Missing dates and jurisdictions are never supplied from today's date. Superseded or partial commencement records are withheld where the dataset cannot establish the exact operative text. `VERIFIED` means local dataset review, not independent live verification of a government page.

`rules.py` selects domains from the persisted intent and evaluates only confirmed facts. It supports a narrow set of typed predicates, preserves missing slots, rule IDs, provision IDs, source IDs, fact IDs, decisions and reasons. Unsupported conditions and narrative exceptions never become true by default. Speed limit lookup is explicitly unresolved because the numeric table has no row level review. No licence or vehicle class equivalence is inferred without dataset support.

`index.py` builds a small, reproducible index over the four base eligible provisions. BM25 ranks lexical matches. The optional multilingual MiniLM embedding model ranks semantic matches; equal weight reciprocal rank fusion combines both rankings. NumPy cosine search is used instead of FAISS because this corpus has only four eligible provision documents. The index manifest stores dataset fingerprint, index version, document hash, model name and revision, retrieval mode and exclusions. A stale or missing index fails clearly. The `--lexical-only` build is an explicit degraded mode; responses expose the actual mode.

`guidance.py` separates `assemble_evidence(matter)` from deterministic `generate(matter)` for Phase 5. The assembled structure contains confirmed facts, intent based query, ranked provisions, rule decisions, eligible procedures and excluded procedure reasons. Guidance uses only eligible provision passages and actual matched rule/fact links. It records evidence IDs, retrieved ranks and scores, source fingerprint, index version, generation method and all rule outcomes. Penalties, numeric speed limits and unresolved procedural steps are withheld. No generative language model is loaded.

## API and frontend

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/legal/status` | Dataset readiness and index capability |
| `POST /api/v1/legal/retrieve` | Development diagnostic retrieval for an existing verified matter ID and revision |
| `POST /api/v1/matters/{id}/guidance` | Revision protected guidance generation and persistence |
| `POST /api/v1/matters/{id}/complete` | Revision protected Summary completion |

The diagnostic retrieval endpoint accepts an existing verified matter, never a caller supplied verification flag. Guidance generation requires `USER_VERIFIED`, persists `GUIDANCE_GENERATED`, and rejects repeat generation. A fact correction invalidates prior guidance and verification and requires renewed user confirmation. The Summary transition is persisted as `COMPLETED`.

The existing Guidance and Summary page layouts now load persisted real matters. Real Guidance calls the backend, shows loading and errors, and never falls back to mock legal content. Demo mode retains mock guidance. Source cards display actual IDs, review status, provision, authority and URL when present. A missing source or mapping shows an explicit limited evidence state. Summary uses persisted guidance and its copy export includes actual provision IDs, evidence IDs and source URLs. Print/save as PDF remains browser printing.

## Commands

From repository root:

```sh
backend/.venv/bin/pip install -r backend/requirements-semantic.txt
backend/.venv/bin/python backend/scripts/build_legal_index.py
backend/.venv/bin/pytest -q backend/tests
npm run lint
npx tsc --noEmit
npm run build
```

For a CPU or network limited machine, run `backend/.venv/bin/python backend/scripts/build_legal_index.py --lexical-only`; this does not claim semantic or hybrid retrieval. The generated index and downloaded model live under ignored `backend/artifacts/legal_index/` and must be rebuilt after source file changes. The embedding model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, Apache-2.0, downloaded from its official model repository.

## Limits and Phase 5 interface

The admissible corpus is only four provisions; zero procedures and zero penalty records qualify. The linked government URLs have not been checked live by this implementation. Matter specific rule applicability can be blocked by missing facts, unresolved vehicle taxonomy, unsupported conditions or narrative exceptions. Reviewed multilingual legal explanations are unavailable. Results are informational and never decide whether an offence occurred. `assemble_evidence` is the structured input boundary for later Llama 3.2 and Mistral 7B comparison; future generators must stay inside its evidence IDs and restrictions. Formal retrieval metrics and model comparison belong to Phase 6.
