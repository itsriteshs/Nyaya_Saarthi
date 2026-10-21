from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.api.legal import verified_matter
from app.schemas.llm import GenerateRequest
from app.schemas.matter import MatterResponse
from app.services import matter_service
from app.services.llm.explanation_service import generate_explanation
from app.services.llm.local_runtime import OllamaProvider
from app.services.llm.model_registry import MODELS, settings

router = APIRouter(tags=["models"])


def _status():
    try:
        config = settings()
    except ValueError:
        return None, {"runtime": "configuration_error", "models": {key: {"status": "configuration_error", "available": False} for key in MODELS}}
    return config, OllamaProvider(config["url"]).availability()


@router.get("/models")
def available_models():
    config, state = _status()
    return {"models": [{"id": key, "displayName": spec.name, "checkpoint": spec.checkpoint,
                         "runtimeName": spec.runtime_name, "license": spec.license,
                         "status": state["models"][key]["status"],
                         "available": state["models"][key]["available"],
                         "default": bool(config and config["default"] == key)} for key, spec in MODELS.items()],
            "runtime": state["runtime"]}


@router.get("/models/health")
def model_health():
    _, state = _status()
    return state


@router.post("/matters/{matter_id}/generate",response_model=MatterResponse,response_model_exclude_none=True)
def generate(matter_id: str, payload: GenerateRequest, session: Session = Depends(get_session)):
    matter = verified_matter(session, matter_id, payload.expectedRevision)
    if matter.guidance and not payload.regenerate:
        raise HTTPException(409, "Guidance exists; set regenerate to true")
    data = matter.model_dump(mode="json")
    # End read transaction before potentially long inference. CAS at save rejects intervening edits/generations.
    session.rollback()
    try:
        data["guidance"] = generate_explanation(data, payload.modelId, payload.language)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(503, str(exc)) from exc
    data["stage"] = "GUIDANCE_GENERATED"
    history = data.get("generationHistory", [])
    if matter.guidance:
        history.append({"revision": payload.expectedRevision, "guidance": matter.guidance.model_dump(mode="json")})
    data["generationHistory"] = history[-10:]
    try:
        return matter_service.save_computed_context(session, matter.id, payload.expectedRevision, data)
    except matter_service.StaleRevision:
        raise HTTPException(409, "Matter revision changed during generation") from None
