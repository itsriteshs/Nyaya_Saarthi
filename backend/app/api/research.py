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


@router.get("/runs/{run_id}/examples")
def examples(run_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",run_id):raise HTTPException(422,"Invalid run ID")
    path=ROOT/"phase7"/run_id
    summary=read(path/"metrics.json")
    if summary is None:raise HTTPException(404,"Run unavailable")
    # Only controlled synthetic studies can expose narrative-bearing rows.
    if "lime" in summary:return {"cases":summary["lime"].get("cases",[])}
    if "rag" in summary:return {"cases":summary["rag"].get("records",[])}
    if "nlp" in summary:
        try:rows=json.loads((path/"nlp_predictions.json").read_text(encoding="utf-8"))
        except (OSError,ValueError):raise HTTPException(404,"Predictions unavailable")
        return {"cases":[{k:r.get(k) for k in ("id","goldIntent","intent","goldLanguage","rawLanguage","policyLanguage")} for r in rows]}
    return {"cases":[],"reason":"No public sanitized examples for this run"}


@router.get("/runs/{run_id}/exports")
def exports(run_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",run_id):raise HTTPException(422,"Invalid run ID")
    folder=ROOT/"phase7"/run_id/"publication"
    return {"files":[p.name for p in sorted(folder.glob("*")) if p.suffix in {".png",".svg",".pdf",".csv",".md"}]}

@router.get("/runs/{run_id}/exports/{filename}")
def download(run_id: str,filename: str):
    from fastapi.responses import FileResponse
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",run_id) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",filename):raise HTTPException(422,"Invalid artifact")
    path=ROOT/"phase7"/run_id/"publication"/filename
    if path.suffix not in {".png",".svg",".pdf",".csv",".md"} or not path.is_file():raise HTTPException(404,"Export unavailable")
    return FileResponse(path,filename=filename)
