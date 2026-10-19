import json
from collections import Counter
from app.config import DATASET_DIR, REPORT_DIR
from app.services.dataset_validator import audit_dataset

def main():
    report = audit_dataset(DATASET_DIR)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "dataset_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Dataset audit", "", f"Run: {report['run_at']}", "", "## Summary", ""]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Files", "", "| Dataset | Records seen | Parsed rows | Columns | IDs |", "|---|---:|---:|---:|---:|"]
    for data in report["datasets"]:
        lines.append(f"| {data['name']} | {data['records_seen']} | {data['rows']} | {data['columns']} | {data['identifier_count']} |")
    lines += ["", "## Issue counts", ""]
    for code, count in Counter(i["code"] for i in report["issues"]).most_common():
        lines.append(f"- {code}: {count}")
    lines += ["", "Full row-level findings are in `dataset_audit.json`."]
    (REPORT_DIR / "dataset_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scanned {report['summary']['dataset_files']} files, {report['summary']['total_rows']} rows; {report['summary']['critical_errors']} errors, {report['summary']['warnings']} warnings")
    return 1 if report["summary"]["critical_errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
