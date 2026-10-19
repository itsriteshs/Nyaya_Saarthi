"""Export every unresolved reference with source-row context; never edits datasets."""
import csv
import json
from app.config import DATASET_DIR, REPORT_DIR
from app.services.dataset_loader import load_dataset
from app.services.dataset_validator import PRIMARY_IDS


def main():
    report = json.loads((REPORT_DIR / "dataset_audit.json").read_text(encoding="utf-8"))
    sources = {}
    for name in PRIMARY_IDS:
        path = DATASET_DIR / name
        if path.exists():
            _, records = load_dataset(path)
            sources[name] = dict(records)
    fields = ["severity", "code", "dataset", "row", "record_id", "context", "column", "value", "message"]
    inventory = REPORT_DIR / "PHASE1_REFERENCE_INVENTORY.csv"
    count = 0
    with inventory.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for finding in report["issues"]:
            if finding["code"] not in {"UNRESOLVED_PLACEHOLDER_REFERENCE", "MISSING_REFERENCE"}:
                continue
            name, number = finding["dataset"], finding["row"]
            row = sources.get(name, {}).get(number, {})
            writer.writerow({
                "severity": finding["severity"], "code": finding["code"],
                "dataset": name, "row": number,
                "record_id": row.get(PRIMARY_IDS.get(name, ""), "") if isinstance(row, dict) else "",
                "context": (row.get("domain") or row.get("requirement_category") or row.get("relief_type") or row.get("offence_name") or row.get("procedure_name") or row.get("rule_name") or "") if isinstance(row, dict) else "",
                "column": finding["column"], "value": finding["value"], "message": finding["message"],
            })
            count += 1
    original_missing = REPORT_DIR / "PHASE1_ORIGINAL_MISSING_REVIEW.csv"
    with original_missing.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for finding in report["issues"]:
            if finding["code"] not in {"MISSING_REFERENCE", "REFERENCE_TYPE_MISMATCH", "STANDALONE_QUERY_ID"}:
                continue
            if finding["code"] == "MISSING_REFERENCE" and finding["dataset"] == "annotated_utterances.csv":
                continue  # discovered by the expanded Phase 1 verification audit
            name, number = finding["dataset"], finding["row"]
            row = sources.get(name, {}).get(number, {})
            writer.writerow({
                "severity": finding["severity"], "code": finding["code"],
                "dataset": name, "row": number,
                "record_id": row.get(PRIMARY_IDS.get(name, ""), "") if isinstance(row, dict) else "",
                "context": (row.get("domain") or row.get("requirement_category") or row.get("procedure_name") or "") if isinstance(row, dict) else "",
                "column": finding["column"], "value": finding["value"], "message": finding["message"],
            })
    print(f"Wrote {count} reference findings to {inventory}")
    print(f"Reviewed original 16 apparent missing references in {original_missing}")


if __name__ == "__main__":
    main()
