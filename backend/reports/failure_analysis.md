# Phase 6 failure analysis

| Case | Expected | Observed and owner | Resolution |
|---|---|---|---|
| `SYN_SPEED_01`, Llama | Cautious provision mention, no definite outcome | `DEFINITE_OUTCOME` and unlinked claim in English; fallback | Prompt and structural gate retained; unresolved model behavior |
| `SYN_INSURANCE_01`, Llama | Only supported actions shown | Two model action strings were unsupported; omitted while answer accepted | Action allowlist applied |
| Hindi, Llama frozen cases | Hindi answer and correct language tag | 3/3 rejected by language gate | Fallback; multilingual generation quality unresolved |
| Grouped NLP test | Gold-consistent missing-slot sets | 1,570 false positive slots, mostly `USER_ROLE` and `VEHICLE_CLASS` | Schema/annotation mismatch remains; requirements retained |
| `OFF_NO_PUC` | Source-backed penalty record | Missing source ID | Excluded; needs source review |
| `SYN_INSURANCE_01`, Mistral English | Evidence-linked explanation | `UNLINKED_CLAIM` caused rejection | Deterministic fallback; prompt compliance remains weak |
| Browser insurance case, refresh | Persisted matter without rendering error | Server rendered empty provider state while first client render read session storage, causing hydration mismatch | Provider restoration moved to post-hydration effect; Summary redirect waits for restoration |

Per-case LLM and NLP predictions are retained under `experiments/predictions/`; rejected legal text was never displayed as guidance. No expert review was performed.
