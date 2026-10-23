from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.api.matters import valid_id
from app.schemas.nlp import AnalyzeRequest, AnalyzeResponse, MatterAnalyzeRequest
from app.schemas.matter import MatterResponse
from app.services.nlp.pipeline import analyze
from app.services.nlp.matter_adapter import persist_analysis, AnalysisConflict, AnalysisStale

from app.services.nlp.slm_extractor import IntakeFailure

router=APIRouter(tags=['nlp'])

def _run(text,language,reference_datetime):
    try:return analyze(text,language,reference_datetime)
    except IntakeFailure as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from None
    except FileNotFoundError:
        raise HTTPException(status_code=503,detail='NLP model is not trained. Run the backend training commands.') from None

@router.post('/nlp/analyze',response_model=AnalyzeResponse,response_model_exclude_none=True)
def standalone(payload:AnalyzeRequest):
    return _run(payload.text,payload.language,payload.referenceDatetime)

@router.post('/matters/{matter_id}/analyze',response_model=MatterResponse,response_model_exclude_none=True)
def analyze_matter(matter_id:str,payload:MatterAnalyzeRequest,session:Session=Depends(get_session)):
    from app.services.matter_service import get_matter
    matter=get_matter(session,valid_id(matter_id))
    if matter is None:raise HTTPException(status_code=404,detail='Matter not found')
    if matter.revision!=payload.revision:raise HTTPException(status_code=409,detail='Matter revision is stale')
    if matter.stage!='DRAFT' or matter.verifiedAt or matter.guidance:
        raise HTTPException(status_code=409,detail='Only a DRAFT matter can be analyzed; create a new matter to reanalyze')
    result=_run(matter.originalText,matter.language,payload.referenceDatetime)
    try:return persist_analysis(session,matter,result)
    except AnalysisConflict:raise HTTPException(status_code=409,detail='Matter can no longer be analyzed') from None
    except AnalysisStale:raise HTTPException(status_code=409,detail='Matter revision is stale') from None
