import csv
import json
from pathlib import Path

EXPECTED_FILES = (
    "accident_relief_and_claims.csv", "adaptive_conversations.jsonl", "annotated_utterances.csv",
    "case_law_interpretations.csv", "coverage_registry.csv", "document_requirements.csv",
    "gold_evaluation_cases.csv", "intents.csv", "jurisdictions.csv", "legal_provisions.csv",
    "legal_sources.csv", "offences_penalties.csv", "official_forms.csv", "official_services.csv",
    "plain_language_multilingual.csv", "procedure_steps.csv", "procedures.csv",
    "query_provision_relevance.csv", "rule_logic.csv", "safety_challenge_cases.csv",
    "slot_schema.csv", "speed_limits.csv", "vehicle_classes.csv",
)

class DatasetReadError(ValueError):
    pass

def load_dataset(path: Path):
    """Return (headers, [(physical line, row)]). Preserve malformed records for audit."""
    try:
        if path.suffix == ".jsonl":
            rows = []
            with path.open(encoding="utf-8-sig") as stream:
                for number, line in enumerate(stream, 1):
                    if not line.strip():
                        rows.append((number, None))
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError as exc:
                        rows.append((number, {"__parse_error__": str(exc)}))
                        continue
                    rows.append((number, item))
            headers = list(next((item for _, item in rows if isinstance(item, dict) and "__parse_error__" not in item), {}).keys())
            return headers, rows
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            headers = next(reader, [])
            rows = []
            try:
                for row in reader:
                    if len(row) > len(headers) and all(not cell.strip() for cell in row[len(headers):]):
                        rows.append((reader.line_num, {**dict(zip(headers, row)), "__trailing_empty_columns__": len(row) - len(headers)}))
                    else:
                        rows.append((reader.line_num, dict(zip(headers, row)) if len(row) == len(headers) else {"__column_error__": row}))
            except csv.Error as exc:
                rows.append((reader.line_num, {"__parse_error__": str(exc)}))
            return headers, rows
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetReadError(str(exc)) from exc
