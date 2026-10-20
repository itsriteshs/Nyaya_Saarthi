import json
from pydantic import ValidationError
from app.schemas.llm import Explanation


def parse_response(text: str) -> Explanation:
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("language") in {"en", "hi"}:
            data["language"] = {"en": "english", "hi": "hindi"}[data["language"]]
        return Explanation.model_validate(data)
    except (ValueError, TypeError, ValidationError) as exc:
        raise ValueError("OUTPUT_SCHEMA_INVALID") from exc
