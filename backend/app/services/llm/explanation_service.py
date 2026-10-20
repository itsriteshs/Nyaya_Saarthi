from datetime import datetime, timezone
from app.services.legal.guidance import generate as deterministic_generate
from app.services.llm.evidence import build_package
from app.services.llm.grounding_validator import validate
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.model_registry import MODELS, settings
from app.services.llm.prompt_builder import PROMPT_VERSION, messages, response_schema
from app.services.llm.response_parser import parse_response
from app.services.llm.output_checks import check_language


def generate_explanation(matter: dict, model_id: str, language: str, provider=None):
    config = settings()
    if model_id != "deterministic" and model_id not in MODELS:
        raise ValueError("Unknown model identifier")
    baseline = deterministic_generate(matter)
    metadata = baseline["metadata"]
    metadata.update({"requestedModel": model_id, "requestedLanguage": language,
                     "outputLanguage": "english",
                     "inputLanguage": matter.get("nlpAnalysis", {}).get("language", {}).get("detectedLanguage", matter.get("language")),
                     "promptVersion": PROMPT_VERSION, "runtime": config["provider"],
                     "generationParameters": {"temperature": config["temperature"], "maxTokens": config["maxTokens"],
                                              "seed": 471, "contextTokens": 8192, "format": "Explanation JSON schema"},
                     "generationTimestamp": datetime.now(timezone.utc).isoformat()})
    try:
        package = build_package(matter, baseline, config["contextChars"])
        metadata["evidencePackageId"] = package["fingerprint"]
    except ValueError:
        package = None
        metadata["evidencePackageId"] = None
    if model_id == "deterministic":
        metadata.update({"fallbackUsed": False, "validation": {"accepted": True, "reasonCodes": []}})
        return baseline
    spec = MODELS[model_id]
    metadata.update({"modelCheckpoint": spec.checkpoint, "runtimeModel": spec.runtime_name,
                     "quantization": "Q4_K_M", "fallbackUsed": True})
    if package is None:
        metadata["failureReason"] = "EVIDENCE_CONTEXT_TOO_LARGE"
        metadata["validation"] = {"accepted": False, "reasonCodes": ["EVIDENCE_CONTEXT_TOO_LARGE"], "fallbackRequired": True}
        return baseline
    if not package["evidence"]:
        metadata["failureReason"] = "INSUFFICIENT_ELIGIBLE_EVIDENCE"
        metadata["validation"] = {"accepted": False, "reasonCodes": ["INSUFFICIENT_ELIGIBLE_EVIDENCE"], "fallbackRequired": True}
        return baseline
    provider = provider or OllamaProvider(config["url"])
    availability = provider.availability()["models"][model_id]
    if not availability["available"]:
        metadata["failureReason"] = availability["status"].upper()
        metadata["validation"] = {"accepted": False, "reasonCodes": [metadata["failureReason"]], "fallbackRequired": True}
        return baseline
    metadata["installedDigest"] = availability.get("digest")
    try:
        response = provider.generate(spec.runtime_name, messages(package, matter["originalText"], language),
                                     temperature=config["temperature"], max_tokens=config["maxTokens"],
                                     timeout=config["timeout"], output_schema=response_schema(package,language))
        metadata.update({"latencyMs": response.duration_ms, "promptTokens": response.prompt_tokens,
                         "outputTokens": response.output_tokens, "reportedRuntimeModel": response.model_digest})
        output = parse_response(response.text)
        check_language(output, language)
        validation = validate(output, package)
        metadata["validation"] = validation
        if not validation["accepted"]:
            metadata["failureReason"] = ",".join(validation["reasonCodes"])
            return baseline
        output.recommendedActions = [action for action in output.recommendedActions
                                     if action in {step["title"] for step in baseline["nextSteps"]}]
        citation_ids = sorted({ref for claim in output.legalClaims for ref in claim.evidenceIds})
        baseline["directAnswer"] = output.answer + "\n\n" + output.explanation + "\n\nEvidence: " + ", ".join(citation_ids)
        baseline["uncertainties"] = list(dict.fromkeys(baseline["uncertainties"] + output.uncertainties))
        metadata.update({"generationMethod": "LOCAL_LLM", "fallbackUsed": False,
                         "outputLanguage": language,
                         "structuredOutput": output.model_dump(), "citedEvidenceIds": citation_ids})
    except (RuntimeFailure, ValueError) as exc:
        metadata["failureReason"] = str(exc)
        metadata["validation"] = {"accepted": False, "reasonCodes": [metadata["failureReason"]], "fallbackRequired": True}
    return baseline
