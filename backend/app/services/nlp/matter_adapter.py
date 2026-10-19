"""Atomic NLP-to-matter mapping. The full canonical result is stored separately."""
from datetime import datetime,timezone
import json
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.db.models import MatterRecord
from app.schemas.matter import MatterResponse
from app.schemas.nlp import AnalyzeResponse
from app.services.matter_service import get_matter
from app.services.conversation import initialize

class AnalysisConflict(Exception):pass
class AnalysisStale(Exception):pass

def persist_analysis(session:Session,matter:MatterResponse,result:AnalyzeResponse)->MatterResponse:
    record=session.get(MatterRecord,matter.id)
    if record is None or record.stage!='DRAFT':raise AnalysisConflict()
    if record.revision!=matter.revision:raise AnalysisStale()
    context=json.loads(record.context_json)
    facts=[]
    for index,e in enumerate(result.entities):
        facts.append({'id':f"{e.type.lower()}_{index}", 'key':e.type,'label':e.type.replace('_',' ').title(),
                      'value':e.text,'state':'provided','provenance':'USER_PROVIDED',
                      'confirmed':False,'requiresConfirmation':True})
    context.update({'intent':{'label':result.intent.name.replace('_',' ').title(),
                              'descriptor':f"{result.intent.domain} · {result.intent.id}"},
                    'facts':facts,'missingSlots':[x.slot for x in result.missingSlots],
                    'contextReadiness':{'found':result.readiness.found,'total':result.readiness.total},
                    'stage':'NEEDS_CLARIFICATION' if result.missingSlots or result.unresolvedSlots or result.intent.needsClarification else 'READY_FOR_REVIEW',
                    'nlpAnalysis':result.model_dump(mode='json',exclude_none=True),
                    'messages':[{'id':'user-initial','speaker':'user','text':matter.originalText},
                                {'id':'assistant-analysis','speaker':'assistant','text':'I identified possible facts and missing context. Please review the extracted details.'}]})
    initialize(context)
    now=datetime.now(timezone.utc)
    MatterResponse.model_validate({**context,'updatedAt':now,'revision':matter.revision+1,'schemaVersion':record.schema_version})
    changed=session.execute(update(MatterRecord).where(MatterRecord.id==matter.id,MatterRecord.revision==matter.revision,MatterRecord.stage=='DRAFT').values(
        context_json=json.dumps(context,ensure_ascii=False),stage=context['stage'],revision=matter.revision+1,updated_at=now))
    if changed.rowcount!=1:
        session.rollback();raise AnalysisStale()
    session.commit()
    return get_matter(session,matter.id)
