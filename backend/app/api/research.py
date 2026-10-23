"""Read-only research endpoints. Evaluation never runs in an HTTP request."""
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import BACKEND_DIR
from app.db.database import get_session
from app.api.matters import valid_id
from app.services.matter_service import get_matter
from app.services.research.trace import trace

router = APIRouter(prefix="/research", tags=["research"])
ROOT = BACKEND_DIR / "experiments"
def read(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None

@router.get("/catalog")
def catalog():
    return {"schemaVersion": 1,
            "historical": {"label": "Historical Phase 6 — exploratory",
                "caveat": "Pending annotation review; grouped test exposed during development. Separate datasets; no overall score. Citation validity is not semantic support. No blinded human ratings.",
                "ablations": read(ROOT/"metrics/phase6_ablations.json"),
                "nlp": read(ROOT/"metrics/phase6_nlp.json"),
                "retrieval": read(ROOT/"metrics/phase6_retrieval.json")},
            "runs": [{"id": p.parent.name, "summary": read(p)} for p in sorted((ROOT/"phase7").glob("*/metrics.json"))],
            "nli": {"status":"unavailable","reason":"No configured license-reviewed local NLI checkpoint; no downloads occur."}}

@router.get("/runs/{run_id}")
def run(run_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise HTTPException(422, "Invalid run identifier")
    result = read(ROOT/"phase7"/run_id/"metrics.json")
    if result is None:
        raise HTTPException(404, "Research artifact unavailable or invalid")
    return result

@router.get("/matters/{matter_id}/trace")
def matter_trace(matter_id: str, session: Session = Depends(get_session)):
    matter = get_matter(session, valid_id(matter_id))
    if matter is None:
        raise HTTPException(404, "Matter not found")
    return trace(matter.model_dump(mode="json"))
