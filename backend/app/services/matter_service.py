from datetime import datetime, timezone
import json
from uuid import uuid4
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.db.models import MatterRecord
from app.schemas.matter import MatterCreate, MatterPatch, MatterResponse

class StaleRevision(Exception):
    pass

def _response(record: MatterRecord) -> MatterResponse:
    return MatterResponse.model_validate({**json.loads(record.context_json), "schemaVersion": record.schema_version, "revision": record.revision, "updatedAt": record.updated_at})

def create_matter(session: Session, payload: MatterCreate) -> MatterResponse:
    now = datetime.now(timezone.utc)
    context = {
        "id": str(uuid4()), "originalText": payload.originalText, "language": payload.language,
        "intent": {"label": "", "descriptor": ""}, "facts": [], "missingSlots": [],
        "contextReadiness": {"found": 0, "total": 0}, "stage": "DRAFT",
        "createdAt": now.isoformat(), "answers": {}, "messages": [],
    }
    record = MatterRecord(id=context["id"], original_text=payload.originalText, language=payload.language, stage="DRAFT", context_json=json.dumps(context), created_at=now, updated_at=now)
    session.add(record)
    session.commit()
    return _response(record)

def get_matter(session: Session, matter_id: str) -> MatterResponse | None:
    record = session.get(MatterRecord, matter_id)
    return _response(record) if record else None

def patch_matter(session: Session, matter_id: str, payload: MatterPatch) -> MatterResponse | None:
    record = session.get(MatterRecord, matter_id)
    if not record:
        return None
    if record.revision != payload.revision:
        raise StaleRevision()
    context = json.loads(record.context_json)
    for key, value in payload.model_dump(exclude_unset=True, exclude={"revision"}, mode="json").items():
        if value is None:
            context.pop(key, None)
        else:
            context[key] = value
    MatterResponse.model_validate({**context, "revision": record.revision + 1, "schemaVersion": record.schema_version, "updatedAt": datetime.now(timezone.utc)})
    now = datetime.now(timezone.utc)
    result = session.execute(update(MatterRecord).where(MatterRecord.id == matter_id, MatterRecord.revision == payload.revision).values(context_json=json.dumps(context), stage=context["stage"], revision=payload.revision + 1, updated_at=now))
    if result.rowcount != 1:
        session.rollback()
        raise StaleRevision()
    session.commit()
    return get_matter(session, matter_id)

def delete_matter(session: Session, matter_id: str) -> bool:
    record = session.get(MatterRecord, matter_id)
    if not record:
        return False
    session.delete(record)
    session.commit()
    return True
