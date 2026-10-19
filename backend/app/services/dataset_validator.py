"""Offline, read-only dataset audit. A warning never certifies legal accuracy."""
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from app.services.dataset_loader import EXPECTED_FILES, DatasetReadError, load_dataset
from app.services.dataset_relationships import RELATIONSHIPS

PRIMARY_IDS = {
    "accident_relief_and_claims.csv": "relief_rule_id", "adaptive_conversations.jsonl": "conversation_id",
    "annotated_utterances.csv": "utterance_id", "case_law_interpretations.csv": "case_id",
    "coverage_registry.csv": "coverage_id", "document_requirements.csv": "requirement_id",
    "gold_evaluation_cases.csv": "eval_id", "intents.csv": "intent_id",
    "jurisdictions.csv": "jurisdiction_id", "legal_provisions.csv": "provision_id",
    "legal_sources.csv": "source_id", "offences_penalties.csv": "offence_id",
    "official_forms.csv": "form_id", "official_services.csv": "service_id",
    "plain_language_multilingual.csv": "explanation_id", "procedure_steps.csv": "procedure_step_id",
    "procedures.csv": "procedure_id", "query_provision_relevance.csv": "pair_id",
    "rule_logic.csv": "rule_id", "safety_challenge_cases.csv": "challenge_id",
    "slot_schema.csv": "slot_id", "speed_limits.csv": "speed_rule_id",
    "vehicle_classes.csv": "vehicle_class_id",
}
REVIEW_COLUMNS = ("review_status", "legal_review_status", "language_review_status", "human_review_status")
DATE_COLUMNS = {"effective_from", "effective_to", "last_verified_at", "valid_from", "valid_to", "decision_date", "event_date", "latest_source_date"}
PLACEHOLDER = re.compile(r"PENDING|NOT_VERIFIED|NOT_REVIEWED|TO_BE_ADDED|TBD", re.I)

def references(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if not isinstance(value, str):
        return [str(value)]
    value = value.strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return references(parsed)
        except json.JSONDecodeError:
            pass
    return [x.strip() for x in re.split(r"[|;]", value) if x.strip()]

def review_label(row):
    values = [str(row[c]).strip().lower() for c in (*REVIEW_COLUMNS, "legal_reviewer") if c in row and row[c] is not None and str(row[c]).strip()]
    if not values:
        return "unknown"
    if any("not_verified" in x or "not_reviewed" in x or "unverified" in x for x in values):
        return "not_verified"
    if any("pending" in x or "under_review" in x or "needs_review" in x or "draft" in x for x in values):
        return "pending_review"
    if all(x in {"verified", "reviewed", "approved", "human_verified", "legal_verified"} for x in values):
        return "verified"
    return "unknown"

def audit_dataset(directory: Path):
    issues = []
    tables = {}
    datasets = []
    def issue(severity, dataset, row, column, code, message, value=None):
        issues.append({"severity": severity, "dataset": dataset, "row": row, "column": column, "code": code, "message": message, "value": value})
    actual = {p.name for p in directory.iterdir() if p.is_file()} if directory.exists() else set()
    for name in EXPECTED_FILES:
        path = directory / name
        if not path.is_file():
            issue("ERROR", name, None, None, "MISSING_FILE", "Expected dataset is missing")
            continue
        try:
            headers, rows = load_dataset(path)
        except DatasetReadError:
            issue("ERROR", name, None, None, "UNREADABLE_FILE", "Dataset cannot be decoded or read")
            continue
        if not headers:
            issue("ERROR", name, 1, None, "MISSING_HEADERS", "No usable header or JSONL object found")
        if len(set(headers)) != len(headers):
            issue("ERROR", name, 1, None, "DUPLICATE_HEADERS", "Duplicate column names")
        if not rows:
            issue("ERROR", name, None, None, "EMPTY_DATASET", "Dataset has no records")
        pk = PRIMARY_IDS[name]
        if headers and pk not in headers:
            issue("ERROR", name, 1, pk, "MISSING_PRIMARY_COLUMN", "Primary identifier column is absent")
        seen_ids = set()
        seen_records = set()
        valid = []
        missing = Counter()
        verification = Counter()
        for row_number, row in rows:
            if row is None:
                issue("WARNING", name, row_number, None, "EMPTY_ROW", "Blank JSONL line")
                continue
            if not isinstance(row, dict) or "__parse_error__" in row or "__column_error__" in row:
                issue("ERROR", name, row_number, None, "MALFORMED_RECORD", "Record cannot be parsed or has inconsistent column count", {"expected_columns": len(headers), "actual_columns": len(row["__column_error__"]), "fields": row["__column_error__"]} if isinstance(row, dict) and "__column_error__" in row else row.get("__parse_error__") if isinstance(row, dict) else None)
                continue
            if "__trailing_empty_columns__" in row:
                count = row.pop("__trailing_empty_columns__")
                issue("WARNING", name, row_number, None, "TRAILING_EMPTY_COLUMNS", f"Record has {count} extra empty trailing column(s)")
            if name.endswith(".jsonl") and set(row) != set(headers):
                issue("WARNING", name, row_number, None, "COLUMN_VARIATION", "JSONL keys differ from first record")
            if not any(str(v).strip() for v in row.values() if v is not None):
                issue("WARNING", name, row_number, None, "EMPTY_ROW", "All values are blank")
                continue
            valid.append((row_number, row))
            identifier = str(row.get(pk, "") or "").strip()
            if not identifier:
                issue("ERROR", name, row_number, pk, "BLANK_PRIMARY_ID", "Primary identifier is blank")
            elif identifier in seen_ids:
                issue("ERROR", name, row_number, pk, "DUPLICATE_PRIMARY_ID", "Primary identifier repeats", identifier)
            seen_ids.add(identifier)
            signature = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
            if signature in seen_records:
                issue("WARNING", name, row_number, None, "DUPLICATE_RECORD", "Exact record repeats")
            seen_records.add(signature)
            for col, val in row.items():
                if val is None or val == "":
                    missing[col] += 1
                if col.endswith("_json") and val not in (None, ""):
                    try:
                        json.loads(val) if isinstance(val, str) else val
                    except json.JSONDecodeError:
                        issue("ERROR", name, row_number, col, "INVALID_JSON_FIELD", "Nested JSON cannot be parsed", str(val)[:120])
                if col in DATE_COLUMNS and val not in (None, ""):
                    try:
                        date.fromisoformat(str(val))
                    except ValueError:
                        issue("WARNING", name, row_number, col, "INVALID_DATE", "Expected ISO date", str(val)[:80])
            start, end = row.get("effective_from"), row.get("effective_to")
            if start and end:
                try:
                    if date.fromisoformat(str(start)) > date.fromisoformat(str(end)):
                        issue("ERROR", name, row_number, "effective_to", "INVALID_EFFECTIVE_RANGE", "End precedes start", end)
                except ValueError:
                    pass
            for col in ("official_url", "official_judgment_url"):
                if row.get(col):
                    parsed = urlparse(str(row[col]))
                    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                        issue("WARNING", name, row_number, col, "INVALID_URL", "Official source URL has invalid syntax", row[col])
            verification[review_label(row)] += 1
        datasets.append({"name": name, "format": path.suffix.lstrip("."), "records_seen": len(rows), "rows": len(valid), "malformed_records": sum(isinstance(row, dict) and ("__parse_error__" in row or "__column_error__" in row) for _, row in rows), "columns": len(headers), "primary_id": pk, "identifier_count": len(seen_ids - {""}), "missing_values": dict(missing), "verification": dict(verification)})
        tables[name] = valid
    for extra in sorted(actual - set(EXPECTED_FILES)):
        issue("INFO", extra, None, None, "UNEXPECTED_FILE", "File is outside the expected collection")
    ids = {name: {str(row.get(PRIMARY_IDS[name], "")).strip() for _, row in records} - {""} for name, records in tables.items()}
    for rel in RELATIONSHIPS:
        if rel.target in tables and rel.target_id != PRIMARY_IDS[rel.target]:
            ids[(rel.target, rel.target_id)] = {str(row.get(rel.target_id, "")).strip() for _, row in tables[rel.target]} - {""}
    checks = []
    for rel in RELATIONSHIPS:
        if rel.source not in tables or rel.target not in tables:
            continue
        count = Counter()
        for number, row in tables[rel.source]:
            if rel.column not in row:
                issue("ERROR", rel.source, number, rel.column, "MISSING_RELATIONSHIP_COLUMN", "Declared relationship column absent")
                continue
            values = references(row[rel.column])
            if not values:
                count["optional_empty" if rel.optional else "required_empty"] += 1
                if not rel.optional:
                    issue("ERROR", rel.source, number, rel.column, "REQUIRED_REFERENCE_EMPTY", "Required association is blank", row[rel.column])
                continue
            for value in values:
                if any(value.startswith(prefix) for prefix in rel.standalone_prefixes):
                    count["standalone"] += 1
                    if not str(row.get("query_text", "")).strip():
                        issue("ERROR", rel.source, number, "query_text", "STANDALONE_QUERY_TEXT_EMPTY", "Standalone query needs its own text", "")
                    else:
                        issue("INFO", rel.source, number, rel.column, "STANDALONE_QUERY_ID", "Synthetic query is defined by this relevance row, not the annotation table", value)
                elif rel.target == "document_requirements.csv" and value.startswith("FORM_"):
                    count["type_mismatch"] += 1
                    form_exists = value in ids.get("official_forms.csv", set())
                    issue("WARNING", rel.source, number, rel.column, "REFERENCE_TYPE_MISMATCH", "Form ID is stored in a document-requirement field" + ("; form exists in official_forms.csv" if form_exists else "; form is also absent from official_forms.csv"), value)
                elif PLACEHOLDER.search(value):
                    count["placeholder"] += 1
                    issue("WARNING", rel.source, number, rel.column, "UNRESOLVED_PLACEHOLDER_REFERENCE", "Reference is an unfinished placeholder", value)
                elif value not in ids[(rel.target, rel.target_id) if rel.target_id != PRIMARY_IDS[rel.target] else rel.target]:
                    count["missing"] += 1
                    issue("ERROR" if not rel.optional else "WARNING", rel.source, number, rel.column, "MISSING_REFERENCE", f"Reference absent from {rel.target}", value)
                else:
                    count["valid"] += 1
        checks.append({"source": rel.source, "column": rel.column, "target": rel.target, "target_id": rel.target_id, "optional": rel.optional, "encoding": rel.encoding, **dict(count)})
    split_analysis = _special_checks(tables, issue)
    language = defaultdict(Counter)
    verification_summary = Counter()
    review_dimensions = defaultdict(lambda: defaultdict(Counter))
    for name, records in tables.items():
        for _, row in records:
            if row.get("language"):
                language[name][str(row["language"]).strip().lower()] += 1
            verification_summary[review_label(row)] += 1
            for col in (*REVIEW_COLUMNS, "legal_reviewer"):
                if col in row:
                    review_dimensions[name][col][str(row[col] or "").strip().lower() or "(blank)"] += 1
    counts = Counter(i["severity"] for i in issues)
    codes = Counter(i["code"] for i in issues)
    return {"run_at": datetime.now(timezone.utc).isoformat(), "summary": {"dataset_files": len(datasets), "expected_files": len(EXPECTED_FILES), "records_seen": sum(d["records_seen"] for d in datasets), "total_rows": sum(d["rows"] for d in datasets), "critical_errors": counts["ERROR"], "warnings": counts["WARNING"], "info": counts["INFO"], "issue_codes": dict(codes)}, "datasets": datasets, "relationship_checks": checks, "language_distribution": {k: dict(v) for k, v in language.items()}, "verification_summary": dict(verification_summary), "review_dimensions": {name: {col: dict(values) for col, values in fields.items()} for name, fields in review_dimensions.items()}, "split_analysis": split_analysis, "issues": issues}

def _special_checks(tables, issue):
    split_examples = defaultdict(list)
    for name in ("annotated_utterances.csv", "gold_evaluation_cases.csv", "adaptive_conversations.jsonl"):
        for number, row in tables.get(name, []):
            text = row.get("text") or row.get("natural_query") or row.get("initial_query") or ""
            split = row.get("split") or row.get("evaluation_split") or ""
            if text and split:
                split_examples[re.sub(r"\s+", " ", str(text).strip().lower())].append({"dataset": name, "row": number, "split": str(split).lower(), "scenario_id": row.get("scenario_id")})
            for col in ("entity_annotations_json", "expected_entities_json"):
                if col not in row or not row[col]:
                    continue
                try:
                    entities = json.loads(row[col]) if isinstance(row[col], str) else row[col]
                    if not isinstance(entities, list):
                        raise ValueError()
                except (ValueError, TypeError):
                    issue("ERROR", name, number, col, "INVALID_ENTITY_STRUCTURE", "Expected JSON entity array")
                    continue
                for entity in entities:
                    if not isinstance(entity, dict):
                        issue("ERROR", name, number, col, "INVALID_ENTITY_STRUCTURE", "Entity is not an object")
                        continue
                    start, end, value = entity.get("start"), entity.get("end"), entity.get("value")
                    if isinstance(start, int) and isinstance(end, int):
                        if not (0 <= start < end <= len(text)):
                            issue("WARNING", name, number, col, "ENTITY_SPAN_OUT_OF_RANGE", "Entity offsets outside text", entity)
                        elif isinstance(value, str) and value and not any(text[a:b] == value for a, b in ((start,end),(start-1,end),(start,end+1),(start-1,end+1)) if 0 <= a < b <= len(text)):
                            issue("WARNING", name, number, col, "ENTITY_SPAN_MISMATCH", "Span differs under common offset conventions", entity)
    for number, row in tables.get("adaptive_conversations.jsonl", []):
        turns = row.get("turns")
        if not isinstance(turns, list) or not turns or any(not isinstance(t, dict) or t.get("speaker") not in {"user", "assistant", "system"} or not isinstance(t.get("text"), str) for t in turns):
            issue("ERROR", "adaptive_conversations.jsonl", number, "turns", "INVALID_TURNS", "Conversation needs nonempty user/assistant turns")
    for number, row in tables.get("query_provision_relevance.csv", []):
        if str(row.get("relevance_label", "")) not in {"0", "1", "2", "3"}:
            issue("WARNING", "query_provision_relevance.csv", number, "relevance_label", "UNEXPECTED_RELEVANCE_LABEL", "Inspect relevance label", row.get("relevance_label"))
    leaked = [(text, records) for text, records in split_examples.items() if len({r["split"] for r in records}) > 1]
    for text, records in leaked[:100]:
        issue("WARNING", "evaluation", None, "split", "POTENTIAL_SPLIT_LEAKAGE", f"Identical normalized text occurs in splits {sorted({r['split'] for r in records})}", text[:120])
    if len(leaked) > 100:
        issue("WARNING", "evaluation", None, "split", "ADDITIONAL_SPLIT_LEAKAGE", f"{len(leaked)-100} further duplicate texts across splits")
    same_dataset = sum(any(len({r["split"] for r in records if r["dataset"] == name}) > 1 for name in {r["dataset"] for r in records}) for _, records in leaked)
    gold_train = sum(any(r["dataset"] == "gold_evaluation_cases.csv" for r in records) and any(r["split"] == "train" for r in records) for _, records in leaked)
    return {"cross_split_texts": len(leaked), "within_dataset_cross_split_texts": same_dataset, "gold_test_texts_also_in_train": gold_train,
            "examples": [{"text": text[:240], "records": records[:12]} for text, records in leaked[:100]]}
