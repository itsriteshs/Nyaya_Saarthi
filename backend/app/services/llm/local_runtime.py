"""Minimal Ollama HTTP adapter; no model download or external request."""
import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from app.services.llm.provider import Generation


class RuntimeFailure(Exception):
    pass


class OllamaProvider:
    def __init__(self, url: str):
        self.url = url

    def _request(self, path: str, payload=None, timeout=2):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.url + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeFailure("MODEL_NOT_INSTALLED" if exc.code == 404 else "MODEL_LOAD_ERROR") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise RuntimeFailure("INFERENCE_TIMEOUT") from exc
        except URLError as exc:
            raise RuntimeFailure("INFERENCE_TIMEOUT" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "RUNTIME_UNREACHABLE") from exc
        except (OSError, ValueError) as exc:
            raise RuntimeFailure("RUNTIME_UNREACHABLE") from exc

    def availability(self):
        from app.services.llm.model_registry import MODELS
        try:
            tags = self._request("/api/tags")
        except RuntimeFailure:
            return {"runtime": "unreachable", "models": {key: {"status": "runtime_unreachable", "available": False} for key in MODELS}}
        installed = {model.get("name"): model for model in tags.get("models", [])}
        return {"runtime": "available", "models": {
            key: {"status": "available" if spec.runtime_name in installed else "not_installed",
                  "available": spec.runtime_name in installed,
                  "digest": installed.get(spec.runtime_name, {}).get("digest"),
                  "sizeBytes": installed.get(spec.runtime_name, {}).get("size")}
            for key, spec in MODELS.items()}}

    def generate(self, model_name, messages, *, temperature, max_tokens, timeout):
        start = time.monotonic()
        response = self._request("/api/chat", {"model": model_name, "messages": messages,
            "stream": False, "format": "json", "options": {"temperature": temperature,
            "num_predict": max_tokens}}, timeout=timeout)
        return Generation(text=response.get("message", {}).get("content", ""),
                          duration_ms=round((time.monotonic() - start) * 1000),
                          prompt_tokens=response.get("prompt_eval_count"),
                          output_tokens=response.get("eval_count"), model_digest=response.get("model"))
