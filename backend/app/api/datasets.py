import json
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from app.config import DATASET_DIR, REPORT_DIR
from app.services.dataset_loader import EXPECTED_FILES, DatasetReadError, load_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

@lru_cache(maxsize=1)
def _summary():
    datasets = []
    for name in EXPECTED_FILES:
        try:
            headers, rows = load_dataset(DATASET_DIR / name)
        except DatasetReadError:
            raise HTTPException(status_code=503, detail=f"Dataset unavailable: {name}") from None
        datasets.append({"name": name, "format": name.rsplit(".", 1)[-1], "rows": sum(isinstance(row, dict) and not any(k.startswith("__parse_error__") or k == "__column_error__" for k in row) for _, row in rows), "columns": len(headers)})
    return {"dataset_count": len(datasets), "datasets": datasets}

@router.get("/summary")
def summary():
    return _summary()

@router.get("/validation")
def validation():
    path = REPORT_DIR / "dataset_audit.json"
    if not path.is_file():
        return {"status": "not_run", "last_audit": None}
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        return {"status": "completed", "last_audit": report["run_at"], "critical_errors": report["summary"]["critical_errors"], "warnings": report["summary"]["warnings"], "file_count": report["summary"]["dataset_files"], "datasets": [{"name": item["name"], "rows": item["rows"]} for item in report["datasets"]]}
    except (OSError, KeyError, ValueError):
        raise HTTPException(status_code=503, detail="Audit report unavailable") from None
