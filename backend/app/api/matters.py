from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.schemas.matter import MatterCreate, MatterPatch, MatterResponse
from app.services import matter_service

router = APIRouter(prefix="/matters", tags=["matters"])

def valid_id(matter_id: str) -> str:
    try:
        return str(UUID(matter_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid matter ID") from None

@router.post("", response_model=MatterResponse, status_code=201)
def create(payload: MatterCreate, session: Session = Depends(get_session)):
    return matter_service.create_matter(session, payload)

@router.get("/{matter_id}", response_model=MatterResponse)
def retrieve(matter_id: str, session: Session = Depends(get_session)):
    result = matter_service.get_matter(session, valid_id(matter_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Matter not found")
    return result

@router.patch("/{matter_id}", response_model=MatterResponse)
def patch(matter_id: str, payload: MatterPatch, session: Session = Depends(get_session)):
    try:
        result = matter_service.patch_matter(session, valid_id(matter_id), payload)
    except matter_service.StaleRevision:
        raise HTTPException(status_code=409, detail="Matter revision is stale") from None
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid matter context") from None
    if result is None:
        raise HTTPException(status_code=404, detail="Matter not found")
    return result

@router.delete("/{matter_id}", status_code=204)
def delete(matter_id: str, session: Session = Depends(get_session)):
    if not matter_service.delete_matter(session, valid_id(matter_id)):
        raise HTTPException(status_code=404, detail="Matter not found")
    return Response(status_code=204)
