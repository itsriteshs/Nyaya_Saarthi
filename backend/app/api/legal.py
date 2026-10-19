from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.api.matters import valid_id
from app.services import matter_service
from app.services.legal.guidance import generate, readiness
from app.services.legal.index import load_manifest, retrieve
from app.services.legal.rules import context, candidates
from app.services.legal.knowledge import load_knowledge

router=APIRouter(tags=['legal'])

class RevisionRequest(BaseModel):
    revision:int=Field(ge=1)

class RetrievalRequest(RevisionRequest):
    matterId:str
    limit:int=Field(default=5,ge=1,le=20)

def verified_matter(session,matter_id,revision):
    matter=matter_service.get_matter(session,valid_id(matter_id))
    if matter is None:raise HTTPException(404,'Matter not found')
    if matter.revision!=revision:raise HTTPException(409,'Matter revision is stale')
    if matter.stage not in {'USER_VERIFIED','GUIDANCE_GENERATED','COMPLETED'} or not matter.verifiedAt:
        raise HTTPException(409,'Matter must be user verified')
    return matter

@router.get('/legal/status')
def status():
    result=readiness()
    try:
        manifest,_=load_manifest()
        result['index']={k:manifest[k] for k in ('indexVersion','documentCount','retrievalMode','embeddingModel','embeddingModelRevision')}
    except (FileNotFoundError,ValueError,RuntimeError) as exc:
        result['index']={'status':'unavailable','reason':str(exc)}
    return result

@router.post('/legal/retrieve')
def search(payload:RetrievalRequest,session:Session=Depends(get_session)):
    matter=verified_matter(session,payload.matterId,payload.revision)
    data=matter.model_dump(mode='json');facts,jurisdiction,event_date=context(data)
    name=data.get('nlpAnalysis',{}).get('intent',{}).get('name') or data['intent']['label']
    query=' '.join([name]+[str(f.get('normalizedValue') or f['value']) for f in facts.values()])
    domains={r['domain'] for r in candidates(data,load_knowledge())}
    try:return retrieve(query,event_date,jurisdiction,payload.limit,domains)
    except (FileNotFoundError,ValueError,RuntimeError) as exc:raise HTTPException(503,str(exc)) from exc

@router.post('/matters/{matter_id}/guidance')
def guidance(matter_id:str,payload:RevisionRequest,session:Session=Depends(get_session)):
    matter=verified_matter(session,matter_id,payload.revision)
    try:current_version=load_manifest()[0]['indexVersion']
    except (FileNotFoundError,ValueError,RuntimeError) as exc:raise HTTPException(503,str(exc)) from exc
    previous_version=(matter.guidance.metadata or {}).get('indexVersion') if matter.guidance else None
    if matter.stage!='USER_VERIFIED' and previous_version==current_version:
        raise HTTPException(409,'Guidance already generated for this index version')
    data=matter.model_dump(mode='json')
    try:data['guidance']=generate(data)
    except (FileNotFoundError,ValueError,RuntimeError) as exc:raise HTTPException(503,str(exc)) from exc
    data['stage']='GUIDANCE_GENERATED'
    try:return matter_service.save_computed_context(session,matter.id,payload.revision,data)
    except matter_service.StaleRevision:raise HTTPException(409,'Matter revision is stale') from None

@router.post('/matters/{matter_id}/complete')
def complete(matter_id:str,payload:RevisionRequest,session:Session=Depends(get_session)):
    matter=verified_matter(session,matter_id,payload.revision)
    if matter.stage!='GUIDANCE_GENERATED' or not matter.guidance:raise HTTPException(409,'Generate guidance before completing the matter')
    try:current_version=load_manifest()[0]['indexVersion']
    except (FileNotFoundError,ValueError,RuntimeError) as exc:raise HTTPException(503,str(exc)) from exc
    if (matter.guidance.metadata or {}).get('indexVersion')!=current_version:
        raise HTTPException(409,'Guidance source index changed; regenerate guidance')
    data=matter.model_dump(mode='json');data['stage']='COMPLETED'
    try:return matter_service.save_computed_context(session,matter.id,payload.revision,data)
    except matter_service.StaleRevision:raise HTTPException(409,'Matter revision is stale') from None
