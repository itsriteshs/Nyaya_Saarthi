import json
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.db.models import MatterRecord
from app.api.matters import valid_id
from app.schemas.conversation import AnswerRequest,FactEditRequest,RevisionRequest,VerifyRequest
from app.schemas.matter import MatterResponse
from app.services.matter_service import get_matter,save_computed_context,StaleRevision
from app.services import conversation

router=APIRouter(prefix='/matters',tags=['conversation'])

def _load(session,matter_id):
    matter_id=valid_id(matter_id)
    record=session.get(MatterRecord,matter_id)
    if record is None:raise HTTPException(404,'Matter not found')
    context=json.loads(record.context_json)
    if not context.get('nlpAnalysis'):raise HTTPException(409,'Analyze this matter before conversation')
    return record,context

def _save(session,record,revision,context):
    if record.revision!=revision:raise HTTPException(409,'Matter revision is stale')
    try:return save_computed_context(session,record.id,revision,context)
    except StaleRevision:raise HTTPException(409,'Matter revision is stale') from None

@router.get('/{matter_id}/conversation')
def get_conversation(matter_id:str,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    return {'matterId':record.id,'messages':context['messages'],'facts':context['facts'],
            'missingSlots':context['missingSlots'],'currentQuestion':context.get('currentQuestion'),
            'conversation':context.get('conversation'), 'contextReadiness':context['contextReadiness'],
            'stage':context['stage'],'revision':record.revision}

@router.get('/{matter_id}/questions/next')
def next_question(matter_id:str,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    return {'question':context.get('currentQuestion'),'reviewEligible':context.get('conversation',{}).get('reviewEligible',False),
            'revision':record.revision}

@router.post('/{matter_id}/answers',response_model=MatterResponse,response_model_exclude_none=True)
def answer(matter_id:str,payload:AnswerRequest,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    if context['stage'] in {'USER_VERIFIED','GUIDANCE_GENERATED','COMPLETED'}:raise HTTPException(409,'Matter is already verified')
    if record.revision!=payload.revision:raise HTTPException(409,'Matter revision is stale')
    if any(m['id']==payload.messageId for m in context['messages']):raise HTTPException(409,'Duplicate answer')
    try:conversation.apply_answer(context,payload.answer,payload.questionId,payload.messageId,payload.referenceDatetime)
    except ValueError as exc:raise HTTPException(409,str(exc)) from None
    except FileNotFoundError:raise HTTPException(503,'NLP model is not trained. Run the backend training commands.') from None
    return _save(session,record,payload.revision,context)

@router.patch('/{matter_id}/facts/{fact_id}',response_model=MatterResponse,response_model_exclude_none=True)
def edit_fact(matter_id:str,fact_id:str,payload:FactEditRequest,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    if record.revision!=payload.revision:raise HTTPException(409,'Matter revision is stale')
    try:conversation.revise_fact(context,fact_id,payload.value)
    except KeyError:raise HTTPException(404,'Fact not found') from None
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    return _save(session,record,payload.revision,context)

@router.post('/{matter_id}/facts/{fact_id}/confirm',response_model=MatterResponse,response_model_exclude_none=True)
def confirm_fact(matter_id:str,fact_id:str,payload:RevisionRequest,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    if context['stage'] in {'USER_VERIFIED','GUIDANCE_GENERATED','COMPLETED'}:raise HTTPException(409,'Matter is already verified')
    if record.revision!=payload.revision:raise HTTPException(409,'Matter revision is stale')
    try:conversation.confirm_fact(context,fact_id)
    except KeyError:raise HTTPException(404,'Fact not found') from None
    except ValueError as exc:raise HTTPException(409,str(exc)) from None
    return _save(session,record,payload.revision,context)

@router.post('/{matter_id}/verify',response_model=MatterResponse,response_model_exclude_none=True)
def verify(matter_id:str,payload:VerifyRequest,session:Session=Depends(get_session)):
    record,context=_load(session,matter_id)
    if record.revision!=payload.revision:raise HTTPException(409,'Matter revision is stale')
    if context['stage']=='USER_VERIFIED':raise HTTPException(409,'Matter is already verified')
    blockers=conversation.verify(context,payload.acknowledgeUnknowns)
    if blockers:raise HTTPException(409,{'blockers':blockers})
    return _save(session,record,payload.revision,context)
