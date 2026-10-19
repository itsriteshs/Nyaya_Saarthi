import json
from pydantic import ValidationError
from app.schemas.llm import Explanation


def parse_response(text: str) -> Explanation:
    try:
        return Explanation.model_validate(json.loads(text))
    except (ValueError, TypeError, ValidationError) as exc:
        raise ValueError("OUTPUT_SCHEMA_INVALID") from exc
