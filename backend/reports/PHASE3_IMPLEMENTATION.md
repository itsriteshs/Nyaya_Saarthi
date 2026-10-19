# Phase 3 implementation

## Adaptive conversation

After Phase 2 analysis, `app/services/conversation.py` initializes a persistent conversation inside the existing SQLite matter JSON. It uses the detected ontology intent to read that intent's rows in `slot_schema.csv`. Required `intent_context` slots are asked in ascending `ask_priority`, then stable `slot_id` order. Optional slots are not forced. The dataset's `only_when_relevant_to_rule_or_situation` condition does not provide a machine-testable predicate; those rows remain in `unresolvedRequirements` and are not silently promoted or satisfied. The provisional missing AGE schema row remains explicitly unresolved. Question wording and reasons come from the dataset's English, Hindi, and Hinglish templates. Auto mode follows confident per-answer language detection; uncertain input falls back to English.

Each accepted answer is recorded once with a client message ID and expected revision. The service reuses Phase 2 extraction and normalization, plus question-context parsing for short speed, categorical, date, boolean, and plain-text responses. An answer can fill several schema slots. Unknown answers remain in `unknownSlots` and `missingSlots`; the question is not repeated. Unsupported or ambiguous answers leave the active question open. Extracted facts preserve raw value, canonical slot, normalized value/ID, source message, method, provenance, and confirmation state. No numeric confidence is invented.

Different normalized values for one slot create a contradiction with both claims preserved. The system asks the user to clarify and blocks verification until resolution. A fact edit records its previous value in `factHistory`, clears matching contradictions, removes any stale verification/guidance state, and requires a fresh explicit confirmation. This is a structured comparison; temporal sequences can still produce apparent contradictions and require user clarification.

`contextReadiness` counts resolved applicable required slots. `reviewEligible` becomes true when there is no further answerable required question or contradiction. Unknown required slots may remain, so readiness may be below 100% at review. Verification requires every resolved fact to be individually confirmed and unknowns to be explicitly acknowledged. Verification means the user reviewed the structured situation; it does not establish legal applicability. Analyzed matters cannot use the generic Phase 1 PATCH route to bypass these gates.

For input indicating immediate injury, the conversation first displays basic urgent-assistance text and the India emergency number 112. This number was checked against the [Government of India Emergency Response Support System](https://112.gov.in/). It gives no liability or penalty conclusion.

## API

All routes are under `/api/v1/matters/{id}`:

| Method | Suffix | Behavior |
|---|---|---|
| GET | `/conversation` | Read conversation, facts, readiness, stage, and revision |
| GET | `/questions/next` | Read active question without mutating history |
| POST | `/answers` | Accept `revision`, `questionId`, `messageId`, `answer`, optional `referenceDatetime`; update one matter transaction |
| PATCH | `/facts/{fact_id}` | Correct a fact with `revision` and `value` |
| POST | `/facts/{fact_id}/confirm` | Confirm one fact with `revision` |
| POST | `/verify` | Verify with `revision` and optional `acknowledgeUnknowns`; reject blockers |

Reads return 200; stale revisions, duplicate message IDs, wrong questions, and state conflicts return 409; unknown resources return 404; invalid input returns 422. The updated matter includes `conversation`, `currentQuestion`, canonical `nlpAnalysis`, and current facts. There is no separate conversation table.

## Frontend

Understand reloads the matter by ID, shows persisted messages and the backend's current question, and submits answers before updating the UI. Verify reloads the same matter, calls backend fact correction/confirmation/verification routes, and displays all fact categories. The session cache only provides the current matter ID and immediate rendering; backend state is refreshed on page entry. API failures preserve unsent text and the previous saved state. The explicit demo mode retains old mock operations. A verified real matter may navigate to Guidance, which shows a Phase 4 gate rather than fabricated legal output. All five routes and the existing layout remain.

## Data and limits

`slot_schema.csv` drives requirements, priorities and question wording; `intents.csv`, `annotated_utterances.csv`, `jurisdictions.csv`, and `vehicle_classes.csv` underpin Phase 2 predictions and answer normalization. `adaptive_conversations.jsonl`, `gold_evaluation_cases.csv`, and `safety_challenge_cases.csv` were inspected as research/evaluation references and are not replayed or used to hardcode answers. Their annotations remain unreviewed. The 23 source files were not edited.

Coverage remains limited for free-form city names, licence/registration specifics, ambiguous vehicle classes, some Hindi/Hinglish answer forms, and unsupported conditional predicates. The initial classifier may select the wrong detailed intent. The service does not infer facts from absent text, compare time-scoped claims reliably, or decide legal outcomes. Phase 4 can consume `USER_VERIFIED` matters, confirmed facts, acknowledged unknowns, contradiction history, and the original canonical NLP analysis while still independently checking legal sources.
