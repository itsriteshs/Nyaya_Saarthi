"""Controlled local comparison on frozen synthetic Phase 4 evidence packages."""
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from app.config import BACKEND_DIR
from app.services.llm.grounding_validator import validate
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.model_registry import MODELS, settings
from app.services.llm.prompt_builder import PROMPT_VERSION, messages
from app.services.llm.response_parser import parse_response

ROOT = BACKEND_DIR / "experiments"
LANGUAGES = ("english", "hindi", "hinglish")


def score(records):
    durations = [r["latencyMs"] for r in records if r.get("latencyMs") is not None]
    statuses = Counter(r["status"] for r in records)
    total = len(records)
    return {"n": total, "statuses": dict(statuses),
            "acceptedRate": statuses["accepted"] / total if total else None,
            "fallbackRate": (total - statuses["accepted"]) / total if total else None,
            "citationValidityProxyRate": sum(r.get("validation", {}).get("unsupportedCitations") == [] for r in records if r.get("validation")) / sum(bool(r.get("validation")) for r in records) if any(r.get("validation") for r in records) else None,
            "unsupportedActionOmissionCount": sum(len(r.get("validation", {}).get("omittedActions", [])) for r in records),
            "reasonCodes": dict(Counter(code for r in records for code in r.get("validation", {}).get("reasonCodes", []))),
            "latencyMs": {"mean": statistics.mean(durations) if durations else None,
                          "median": statistics.median(durations) if durations else None,
                          "p95": sorted(durations)[max(0, int(.95 * len(durations) + .999999) - 1)] if len(durations) >= 5 else None},
            "meanPromptTokens": statistics.mean(r["promptTokens"] for r in records if r.get("promptTokens") is not None) if any(r.get("promptTokens") is not None for r in records) else None,
            "meanOutputTokens": statistics.mean(r["outputTokens"] for r in records if r.get("outputTokens") is not None) if any(r.get("outputTokens") is not None for r in records) else None}


def run(model_id, trials=1):
    if model_id not in MODELS: raise ValueError("Only configured Llama or Mistral may be compared")
    config = settings()
    spec = MODELS[model_id]
    frozen = json.loads((ROOT / "manifests" / "phase6_evidence_packages.json").read_text(encoding="utf-8"))
    provider = OllamaProvider(config["url"])
    availability = provider.availability()["models"][model_id]
    if not availability["available"]: raise RuntimeError(f"{model_id}: {availability['status']}")
    output = ROOT / "predictions" / f"phase6_llm_{model_id}.jsonl"
    if output.exists(): raise FileExistsError(f"{output} exists; preserve the prior experiment")
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for case in frozen["cases"]:
        for language in LANGUAGES:
            for trial in range(1, trials + 1):
                row = {"caseId": case["caseId"], "modelId": model_id, "checkpoint": spec.checkpoint,
                       "runtimeTag": spec.runtime_name, "installedDigest": availability.get("digest"),
                       "quantization": "Q4_K_M", "language": language, "trial": trial,
                       "evidencePackageId": case["package"]["fingerprint"],
                       "indexVersion": case["package"]["indexVersion"], "promptVersion": PROMPT_VERSION,
                       "temperature": config["temperature"], "maxTokens": config["maxTokens"],
                       "seed": None, "synthetic": True}
                try:
                    result = provider.generate(spec.runtime_name, messages(case["package"], case["question"], language),
                                               temperature=config["temperature"], max_tokens=config["maxTokens"],
                                               timeout=config["timeout"])
                    row.update({"rawOutput": result.text, "latencyMs": result.duration_ms,
                                "promptTokens": result.prompt_tokens, "outputTokens": result.output_tokens})
                    try:
                        parsed = parse_response(result.text)
                        row["parsedOutput"] = parsed.model_dump()
                        verdict = validate(parsed, case["package"])
                        row["validation"] = verdict
                        if parsed.language != language or language == "hindi" and not any("\u0900" <= c <= "\u097f" for c in parsed.answer) or language == "hinglish" and any("\u0900" <= c <= "\u097f" for c in parsed.answer):
                            row["status"] = "language_rejected"
                        else:
                            row["status"] = "accepted" if verdict["accepted"] else "grounding_rejected"
                    except ValueError:
                        row["status"] = "schema_rejected"
                except RuntimeFailure as exc:
                    row["status"] = "runtime_failure"
                    row["runtimeReason"] = str(exc)
                row["fallbackUsed"] = row["status"] != "accepted"
                records.append(row)
                with output.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(json.dumps({"model": model_id, "case": case["caseId"], "language": language,
                                  "status": row["status"], "latencyMs": row.get("latencyMs")} ), flush=True)
    metrics = {"protocol": "One frozen synthetic evidence package per case; identical system prompt, schema, context, languages and generation settings for both models. Ollama supplies model-specific chat templates. Temperature 0; no seed exposed by this adapter; one trial unless specified.",
               "modelId": model_id, "runtimeTag": spec.runtime_name, "installedDigest": availability.get("digest"),
               "promptVersion": PROMPT_VERSION, "evidenceSetVersion": frozen["version"],
               "overall": score(records), "byLanguage": {lang: score([r for r in records if r["language"] == lang]) for lang in LANGUAGES},
               "semanticClaimSupport": None,
               "semanticClaimSupportReason": "No qualified human reviewer scored legal meaning; structural checks are proxies only."}
    path = ROOT / "metrics" / f"phase6_llm_{model_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=tuple(MODELS))
    parser.add_argument("--trials", type=int, default=1)
    args = parser.parse_args()
    if args.trials < 1 or args.trials > 3: parser.error("trials must be between 1 and 3")
    result = run(args.model, args.trials)
    print(json.dumps({"model": result["modelId"], "overall": result["overall"]}, indent=2))
