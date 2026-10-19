import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    runtime_name: str
    checkpoint: str
    license: str


MODELS = {
    "llama3.2-3b": ModelSpec("llama3.2-3b", "Llama 3.2 3B Instruct", "llama3.2:3b-instruct-q4_K_M", "meta-llama/Llama-3.2-3B-Instruct", "Meta Llama 3.2 Community License"),
    "mistral-7b": ModelSpec("mistral-7b", "Mistral 7B Instruct v0.3", "mistral:7b-instruct-v0.3-q4_K_M", "mistralai/Mistral-7B-Instruct-v0.3", "Apache-2.0"),
}


def settings():
    provider = os.getenv("NYAYA_LLM_PROVIDER", "ollama")
    if provider != "ollama":
        raise ValueError("NYAYA_LLM_PROVIDER must be ollama")
    default = os.getenv("NYAYA_LLM_DEFAULT_MODEL", "llama3.2-3b")
    if default not in MODELS:
        raise ValueError("NYAYA_LLM_DEFAULT_MODEL must identify one of the two configured models")
    url = os.getenv("NYAYA_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    if not (url.startswith("http://127.0.0.1:") or url.startswith("http://localhost:")):
        raise ValueError("NYAYA_OLLAMA_URL must point to local Ollama")
    return {"provider": provider, "default": default, "url": url,
            "timeout": max(1, min(float(os.getenv("NYAYA_LLM_TIMEOUT", "90")), 300)),
            "temperature": max(0, min(float(os.getenv("NYAYA_LLM_TEMPERATURE", "0")), 1)),
            "maxTokens": max(128, min(int(os.getenv("NYAYA_LLM_MAX_TOKENS", "700")), 2048)),
            "contextChars": max(2000, min(int(os.getenv("NYAYA_LLM_CONTEXT_CHARS", "12000")), 30000))}
