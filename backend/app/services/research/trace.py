"""Read recorded evidence only. Never rerun models/retrieval to explain old output."""
def trace(matter):
    analysis = matter.get("nlpAnalysis") or {}
    guidance = matter.get("guidance") or {}
    metadata = guidance.get("metadata") or {}
    return {"schemaVersion": 1, "matterId": matter["id"], "revision": matter["revision"],
            "originalText": matter["originalText"], "language": analysis.get("language"),
            "intent": (matter.get("conversation") or {}).get("originalIntentPrediction") or analysis.get("intent"),
            "selectedWorkflow": analysis.get("intent") if (matter.get("conversation") or {}).get("intentConfirmed") else None, "facts": matter.get("facts", []),
            "initialEntities": analysis.get("entities"), "extraction": analysis.get("extractionMetadata"),
            "question": matter.get("currentQuestion"), "missingSlots": matter.get("missingSlots"),
            "conversation": matter.get("conversation"), "messages": matter.get("messages", []),
            "sources": guidance.get("sources"), "mappings": guidance.get("mappings"),
            "retrieval": {k: metadata.get(k) for k in ("retrievalMode","indexVersion","sourceFingerprint",
                         "retrievedEvidence","retrievalExclusions","procedureExclusions","ruleEvaluations")},
            "generation": metadata or None, "answer": guidance.get("directAnswer"),
            "uncertainties": guidance.get("uncertainties"), "nextSteps": guidance.get("nextSteps"),
            "claims": (metadata.get("structuredOutput") or {}).get("legalClaims"),
            "semanticSupport": {"status": "unavailable", "reason": "No configured, license-reviewed local NLI evaluator. Citation validity is not semantic or legal correctness."},
            "limitations": ["Absent fields mean not recorded; historical feature attributions are not reconstructed.",
                           "Only the current question has a guaranteed stored rationale; messages are not a complete historical planner trace.",
                           "User confirmation does not establish legal applicability."]}
