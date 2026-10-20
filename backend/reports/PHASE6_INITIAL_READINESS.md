# Phase 6 initial readiness audit — 19 October 2026

This is a pre-implementation baseline, recorded before Phase 6 code changes. The repository was clean at the start of this phase.

## Confirmed working

- FastAPI imports and responds: `/api/v1/health`, `/api/v1/legal/status`, and `/api/v1/models` returned HTTP 200 in a local TestClient startup check.
- Existing backend suite: 37 passed. Existing Phase 2 exploratory evaluation processed 1,000 derived test rows: intent accuracy 0.924, exact-span entity F1 0.9188, missing-slot F1 0.3232. The evaluation was rerun into `/tmp/nyaya_phase6_baseline_reports`, leaving prior reports intact.
- Intent and language `.joblib` artifacts, split manifest, and hybrid legal index files exist. The legal index reports version `a6183dd22a43ad0b`, source fingerprint `b0521a641e94c970ab3b12b41f66357705feae5acbcf0d3d84cc9dc21ed2cb2c`, and multilingual MiniLM revision `local-sha256:7f4f89d628f87ade0e0b`.
- Python 3.12.6, Node 24.11.1, npm 11.6.2, backend venv, and frontend `node_modules` are present.

## Code and integration gaps to investigate

- No browser-level five-page real-backend journey or printable summary check is recorded in the existing tests.
- The Phase 5 smoke script is one matter at a time; no frozen public research scenario set, aggregate dual-model comparison, retrieval-variant evaluation, or formal ablation outputs are present.
- The current grounding validator checks patterns and citation IDs but cannot establish semantic claim support. Hindi/Hinglish legal meaning has no independent review.
- The existing NLP evaluation uses a previously exposed, synthetic-derived test set; language and missing-slot results are weak and their causes require inspection.

## Data quality and legal coverage

- Re-running the dataset validator found 23 files, 20,213 parsed rows, 2 critical errors, and 341 warnings (expected nonzero exit). The known errors are malformed `procedures.csv` row 26 and missing `OFF_NO_PUC.source_id`. Source data have not been changed.
- There are 4 eligible legal provisions, no admissible affirmative procedure, penalty, or reviewed numeric speed-limit record. Local review labels are not independent legal authentication.
- The 10,000 utterance annotations, 420 gold cases, 3,000 conversations, and relevance judgments remain without the expert review needed for independent benchmark claims. The original text split has overlap concerns despite the derived manifest.

## Model artifacts and environment

- Apple M3, 16 GiB unified memory, 19 GiB available disk space. Ollama 0.35.1 responds locally, but neither selected model tag is installed. Real Llama and Mistral inference is therefore untested at this baseline. A separate approval was requested for the approximately 6.4 GB weight download.
- Artifact SHA-256: intent `92d868be40a454993c08033ca0d019622d1403e6dc0a57f518f5554c1e395bc0`; language `ca6fdc34a9837c006fee7495dc4018406bc1ba07216faeb200f3ddee0fecceda`; split manifest `3242531df2c74cf557c307722ab56253ff73be8d1817e833c5bf56b780ace07b`; index manifest `d05adfd27ae78de300245f24756a49aab1c5a9f01d8cc80b6cd34ba640b92431`.

## Classification of blockers

**Code/integration:** missing research runners and browser-level validation. **Data:** two structural errors, split overlap, unreviewed annotations and limited legal coverage. **Artifacts:** both requested LLM weights absent. **External review:** semantic legal and multilingual quality cannot be certified by automated checks alone.
