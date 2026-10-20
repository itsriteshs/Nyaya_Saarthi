from dataclasses import dataclass
from typing import Protocol


@dataclass
class Generation:
    text: str
    duration_ms: int
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    model_digest: str | None = None


class Provider(Protocol):
    def availability(self) -> dict: ...
    def generate(self, model_name: str, messages: list[dict], *, temperature: float, max_tokens: int, timeout: float, output_schema: dict | None = None) -> Generation: ...
