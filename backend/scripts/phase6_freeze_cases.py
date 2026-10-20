"""Freeze explicit synthetic verified cases and Phase 4 evidence for both LLMs."""
import json
from app.config import BACKEND_DIR
from app.services.legal.guidance import generate
from app.services.llm.evidence import build_package
from app.services.llm.model_registry import settings


CASES = [
    {"id": "SYN_SPEED_01", "intent": "SPEEDING", "question": "What legal provision may regulate speed on an expressway in Tamil Nadu? I do not know the posted limit.",
     "extra": {"ROAD_TYPE": "expressway"}},
    {"id": "SYN_INSURANCE_01", "intent": "INSURANCE", "question": "My car insurance expired in Tamil Nadu. Which provision may be relevant?",
     "extra": {"INSURANCE_STATUS": "expired"}},
    {"id": "SYN_REGISTRATION_01", "intent": "REGISTRATION", "question": "My car registration expired in Tamil Nadu. Which provision may be relevant?",
     "extra": {"RC_STATUS": "expired"}},
]


def run():
    frozen = []
    for case in CASES:
        fact_values = {"STATE": "Tamil Nadu", "EVENT_DATE": "2026-01-01", "VEHICLE_CLASS": "car", **case["extra"]}
        facts = [{"id": f"{case['id']}:{key}", "key": key, "label": key.replace("_", " ").title(), "value": value,
                  "normalizedValue": value, "normalizedId": "JX_IN_TN" if key == "STATE" else "VC_MOTORCAR" if key == "VEHICLE_CLASS" else None,
                  "confirmed": True, "provenance": "USER_CONFIRMED", "resolutionStatus": "resolved"} for key, value in fact_values.items()]
        matter = {"id": case["id"], "originalText": case["question"], "language": "english",
                  "intent": {"label": case["intent"]}, "nlpAnalysis": {"intent": {"name": case["intent"]}},
                  "facts": facts, "missingSlots": []}
        baseline = generate(matter)
        package = build_package(matter, baseline, settings()["contextChars"])
        frozen.append({"caseId": case["id"], "synthetic": True, "question": case["question"],
                       "package": package, "baseline": baseline})
    path = BACKEND_DIR / "experiments" / "manifests" / "phase6_evidence_packages.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": "phase6-synthetic-v1", "cases": frozen}, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path), "cases": [{"caseId": item["caseId"], "evidencePackageId": item["package"]["fingerprint"],
                                          "sourceCount": len(item["package"]["evidence"])} for item in frozen]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
