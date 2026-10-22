"""Freeze the Phase 4 result into a small identical input for either model."""
import hashlib
import json


def build_package(matter: dict, baseline: dict, max_chars: int) -> dict:
    sources = [{"evidenceId": s["evidenceId"], "provisionId": s["id"],
                "provision": s["provision"], "passage": s["relevantPoint"],
                "title": s["title"]} for s in baseline["sources"] if s.get("admissibility") == "eligible"]
    facts = [{"key": f["key"], "value": f.get("normalizedValue") or f["value"], "unit": f.get("unit"), "sourceText": f.get("sourceText") or f["value"]}
             for f in matter["facts"] if f.get("confirmed") and f.get("provenance") == "USER_CONFIRMED"
             and f.get("resolutionStatus", "resolved") == "resolved"]
    rules = baseline["metadata"].get("ruleEvaluations", [])
    safe_rules = [{key: rule.get(key) for key in ("ruleId", "status", "reasons", "provisionId", "matchedFactIds", "missingSlots")}
                  for rule in rules if rule.get("status") in {"MATCHED", "INSUFFICIENT_CONTEXT", "UNSUPPORTED_CONDITION"}]
    package = {"matterId": matter["id"], "intent": matter.get("nlpAnalysis", {}).get("intent", {}).get("name") or matter["intent"]["label"],
               "facts": facts, "unresolvedFacts": matter.get("missingSlots", []),
               "jurisdiction": baseline["metadata"].get("jurisdictionId"),
               "eventDate": baseline["metadata"].get("eventDate"),
               "ruleEvaluations": safe_rules,
               "excludedRuleIds": [rule["ruleId"] for rule in rules if rule.get("status") in {"EXCLUDED_UNVERIFIED", "NOT_MATCHED"}],
               "evidence": sources, "supportedActions": baseline["nextSteps"],
               "uncertainties": baseline["uncertainties"],
               "excludedEvidence": baseline["metadata"].get("retrievalExclusions", []),
               "excludedProcedures": baseline["metadata"].get("procedureExclusions", []),
               "indexVersion": baseline["metadata"]["indexVersion"],
               "sourceFingerprint": baseline["metadata"]["sourceFingerprint"]}
    # Never trim qualifications, uncertainty or evidence in a way that changes meaning.
    serialized = json.dumps(package, sort_keys=True, ensure_ascii=False)
    if len(serialized) > max_chars:
        raise ValueError("EVIDENCE_CONTEXT_TOO_LARGE")
    package["fingerprint"] = hashlib.sha256(serialized.encode()).hexdigest()
    return package
