"""Offline comparison hook: same persisted verified snapshot and evidence for both models.

No matter text, prompt or output is printed. No matter is changed.
"""
import argparse
import json
from app.db.database import SessionLocal
from app.services.matter_service import get_matter
from app.services.legal.guidance import generate as deterministic_generate
from app.services.llm.evidence import build_package
from app.services.llm.local_runtime import OllamaProvider
from app.services.llm.model_registry import MODELS, settings
from app.services.llm.prompt_builder import messages
from app.services.llm.response_parser import parse_response
from app.services.llm.grounding_validator import validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("matter_id")
    parser.add_argument("--language", choices=("english", "hindi", "hinglish"), default="english")
    args = parser.parse_args()
    with SessionLocal() as session:
        record = get_matter(session, args.matter_id)
    if not record or record.stage not in {"USER_VERIFIED", "GUIDANCE_GENERATED", "COMPLETED"} or not record.verifiedAt:
        parser.error("matter must exist and be verified")
    matter = record.model_dump(mode="json")
    config = settings()
    baseline = deterministic_generate(matter)
    package = build_package(matter, baseline, config["contextChars"])
    provider = OllamaProvider(config["url"])
    availability = provider.availability()["models"]
    results = []
    for key, spec in MODELS.items():
        row = {"modelId": key, "checkpoint": spec.checkpoint, "runtimeModel": spec.runtime_name,
               "evidencePackageId": package["fingerprint"], "indexVersion": package["indexVersion"],
               "language": args.language, "temperature": config["temperature"], "maxTokens": config["maxTokens"]}
        if not availability[key]["available"]:
            row.update({"status": availability[key]["status"], "fallbackUsed": True})
        else:
            try:
                response = provider.generate(spec.runtime_name, messages(package, matter["originalText"], args.language),
                                             temperature=config["temperature"], max_tokens=config["maxTokens"], timeout=config["timeout"])
                parsed = parse_response(response.text)
                verdict = validate(parsed, package)
                row.update({"status": "accepted" if verdict["accepted"] else "rejected",
                            "fallbackUsed": not verdict["accepted"], "validation": verdict,
                            "latencyMs": response.duration_ms, "promptTokens": response.prompt_tokens,
                            "outputTokens": response.output_tokens, "installedDigest": availability[key].get("digest")})
            except Exception as exc:
                row.update({"status": type(exc).__name__, "fallbackUsed": True})
        results.append(row)
    print(json.dumps({"matterId": record.id, "baselineMethod": baseline["metadata"]["generationMethod"],
                      "results": results}, indent=2))


if __name__ == "__main__":
    main()
