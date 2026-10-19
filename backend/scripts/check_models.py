"""Read-only local model readiness. No downloads."""
import json
from app.services.llm.local_runtime import OllamaProvider
from app.services.llm.model_registry import MODELS, settings


def main():
    config = settings()
    status = OllamaProvider(config["url"]).availability()
    print(json.dumps({"runtime": status["runtime"], "models": [
        {"id": key, "runtimeName": spec.runtime_name, **status["models"][key]}
        for key, spec in MODELS.items()]}, indent=2))


if __name__ == "__main__":
    main()
