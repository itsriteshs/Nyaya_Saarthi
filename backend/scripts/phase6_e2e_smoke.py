"""Run a synthetic, persistent HTTP journey against an isolated local backend.

Use NYAYA_DATABASE_URL pointing at a disposable SQLite database when starting the
server. This script creates one matter and leaves it available for inspection.
"""
import argparse
import json
from uuid import uuid4
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def run(base_url: str, model_id: str) -> dict:
    base = base_url.rstrip("/") + "/api/v1"
    steps = []

    def call(method, path, payload=None, expected=200):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(base + path, data=body, method=method,
                          headers={"Content-Type": "application/json"} if body else {})
        try:
            with urlopen(request, timeout=180) as response:
                status = response.status
                result = json.load(response)
        except HTTPError as exc:
            status = exc.code
            result = json.loads(exc.read())
        steps.append({"method": method, "path": path.split("?")[0], "status": status})
        if status != expected:
            raise AssertionError(f"{method} {path}: expected {expected}, got {status}: {result}")
        return result

    call("GET", "/health")
    call("GET", "/legal/status")
    call("GET", "/models")
    clarification = call("POST", "/matters", {"originalText": "I was driving at 120 km/h",
                                                   "language": "english"}, 201)
    clarification_path = "/matters/" + clarification["id"]
    clarification = call("POST", clarification_path + "/analyze", {"revision": clarification["revision"]})
    clarification_question = clarification["currentQuestion"]
    assert clarification_question and clarification_question["slot"] in clarification["missingSlots"]
    clarification = call("POST", clarification_path + "/answers",
                         {"revision": clarification["revision"], "questionId": clarification_question["id"],
                          "messageId": str(uuid4()), "answer": "I do not know"})
    assert clarification_question["slot"] in call("GET", clarification_path + "/conversation")["conversation"]["unknownSlots"]
    matter = call("POST", "/matters", {"originalText": "I drove my car at 120 km/h on an expressway in Tamil Nadu on 1 January 2026",
                                           "language": "english"}, 201)
    path = "/matters/" + matter["id"]
    call("POST", path + "/guidance", {"revision": matter["revision"]}, 409)
    matter = call("POST", path + "/analyze", {"revision": matter["revision"]})
    assert matter["nlpAnalysis"] and matter["conversation"]
    assert call("GET", path + "/conversation")["revision"] == matter["revision"]
    question = matter.get("currentQuestion")
    if question:
        matter = call("POST", path + "/answers", {"revision": matter["revision"],
                                                   "questionId": question["id"],
                                                   "messageId": str(uuid4()),
                                                   "answer": "I do not know"})
        assert question["slot"] in matter["conversation"]["unknownSlots"]
    speed = next(f for f in matter["facts"] if f["key"] == "OBSERVED_SPEED")
    matter = call("PATCH", path + "/facts/" + speed["id"],
                  {"revision": matter["revision"], "value": "90 km/h"})
    assert next(f for f in matter["facts"] if f["id"] == speed["id"])["confirmed"] is False
    for fact in list(matter["facts"]):
        if fact.get("resolutionStatus") == "resolved":
            matter = call("POST", path + "/facts/" + fact["id"] + "/confirm",
                          {"revision": matter["revision"]})
    call("POST", path + "/verify", {"revision": matter["revision"] - 1}, 409)
    matter = call("POST", path + "/verify", {"revision": matter["revision"],
                                             "acknowledgeUnknowns": True})
    assert matter["stage"] == "USER_VERIFIED" and matter["verifiedAt"]
    retrieval = call("POST", "/legal/retrieve", {"matterId": matter["id"],
                                                   "revision": matter["revision"]})
    matter = call("POST", path + "/generate", {"modelId": model_id,
                                                "language": "english",
                                                "expectedRevision": matter["revision"]})
    assert matter["stage"] == "GUIDANCE_GENERATED" and matter["guidance"]
    persisted = call("GET", path)
    assert persisted["guidance"] == matter["guidance"]
    call("POST", path + "/complete", {"revision": matter["revision"] - 1}, 409)
    matter = call("POST", path + "/complete", {"revision": matter["revision"]})
    assert matter["stage"] == "COMPLETED"
    return {"matterId": matter["id"], "clarificationMatterId": clarification["id"],
            "clarificationSlot": clarification_question["slot"], "modelId": model_id, "finalStage": matter["stage"],
            "retrievalMode": retrieval["retrievalMode"],
            "retrievedCount": len(retrieval["results"]),
            "generationMethod": matter["guidance"]["metadata"].get("generationMethod"),
            "fallbackUsed": matter["guidance"]["metadata"].get("fallbackUsed"),
            "steps": steps}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--model", default="deterministic",
                        choices=("deterministic", "llama3.2-3b", "mistral-7b"))
    args = parser.parse_args()
    print(json.dumps(run(args.base_url, args.model), indent=2))
