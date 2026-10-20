import json
from pydantic import ValidationError
from app.schemas.llm import Explanation


def parse_response(text: str) -> Explanation:
    try:
        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ValueError('Duplicate JSON key')
                result[key] = value
            return result
        data = json.loads(text, object_pairs_hook=unique_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if isinstance(data, dict) and data.get("language") in {"en", "hi"}:
            data["language"] = {"en": "english", "hi": "hindi"}[data["language"]]
        return Explanation.model_validate(data)
    except (ValueError, TypeError, ValidationError) as exc:
        raise ValueError("OUTPUT_SCHEMA_INVALID") from exc
