# crud.py

from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from app.llm.embeddings import generate_vector_embeddings, EmbeddingError
from app.models.incident import IncidentLog
from app.schemas.incident import IncidentLogCreate, UpdateIncident
from app.security.redaction import redact_text
from sqlalchemy import func, or_


EMBED_MODEL = os.getenv("EMBED_MODEL", "local-deterministic-v1")


def create_incident(db: Session, tenant_id: str, incident: IncidentLogCreate) -> IncidentLog:
    msg_redacted = redact_text(incident.message)

    db_obj = IncidentLog(
        tenant_id=tenant_id,
        service=incident.service,
        severity=incident.severity,
        title=incident.title,
        affected_sys=incident.affected_sys,
        reporter=incident.reporter,
        source=incident.source,
        tags=incident.tags,
        message_raw=incident.message,
        message_redacted=msg_redacted,
        stack_trace=incident.stack_trace,
        embedding_status="pending",
        is_deleted=False,
    )

    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    except SQLAlchemyError as e:
        db.rollback()
        raise e

    try:
        vec, model_name = generate_vector_embeddings(db_obj.message_redacted, model=EMBED_MODEL)
        db_obj.embedding = vec
        db_obj.embedding_model = model_name
        db_obj.embedding_dim = len(vec)
        db_obj.embedding_version = 1
        db_obj.embedding_status = "ready"
        db_obj.embedding_updated_at = func.now()
        db_obj.embedding_error = None
    except EmbeddingError as e:
        db_obj.embedding = None
        db_obj.embedding_model = "local-deterministic-v1"
        db_obj.embedding_dim = None
        db_obj.embedding_version = 1
        db_obj.embedding_status = "failed"
        db_obj.embedding_updated_at = func.now()
        db_obj.embedding_error = str(e)

    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def get_incident_by_id(db: Session, tenant_id: str, incident_id: int, include_deleted: bool = False) -> Optional[IncidentLog]:
    q = db.query(IncidentLog).filter(IncidentLog.tenant_id == tenant_id, IncidentLog.id == incident_id)
    if not include_deleted:
        q = q.filter(IncidentLog.is_deleted == False) 
    return q.first()


def search_incidents(db: Session, tenant_id: str, query: str, top_k: int = 5) -> List[IncidentLog]:
    q_redacted = redact_text(query)
    vec, _model_name = generate_vector_embeddings(q_redacted, model=EMBED_MODEL)


    # 1) Lexical prefilter to avoid totally unrelated results
    like = f"%{query.strip()}%"
    lexical_filter = or_(
        IncidentLog.title.ilike(like),
        IncidentLog.message_redacted.ilike(like),
        IncidentLog.service.ilike(like),
        # tags is array, this is optional and depends on your column type
        # IncidentLog.tags.any(query.strip()),
    )

    # 2) Only consider good rows, then rerank by vector distance
    q = (
        db.query(IncidentLog)
        .filter(
            IncidentLog.tenant_id == tenant_id,
            IncidentLog.is_deleted == False, 
            IncidentLog.embedding_status == "ready",
            IncidentLog.embedding.isnot(None),
        )
        .filter(lexical_filter)
        .order_by(IncidentLog.embedding.cosine_distance(vec))
        .limit(top_k)
    )

    return q.all()


def update_incident(db: Session, tenant_id: str, incident_id: int, update: UpdateIncident) -> Optional[IncidentLog]:
    db_obj = (
        db.query(IncidentLog)
        .filter(
            IncidentLog.tenant_id == tenant_id,
            IncidentLog.id == incident_id,
            IncidentLog.is_deleted == False,  
        )
        .first()
    )
    if not db_obj:
        return None

    payload = update.model_dump(exclude_unset=True)
    message_changed = "message" in payload

    for field, value in payload.items():
        if field == "message":
            db_obj.message_raw = value
            db_obj.message_redacted = redact_text(value)
        else:
            setattr(db_obj, field, value)

    if message_changed:
        db_obj.embedding_status = "pending"
        db_obj.embedding_error = None
        try:
            vec, model_name = generate_vector_embeddings(db_obj.message_redacted, model=EMBED_MODEL)
            db_obj.embedding = vec
            db_obj.embedding_model = model_name
            db_obj.embedding_dim = len(vec)
            db_obj.embedding_version = (db_obj.embedding_version or 0) + 1
            db_obj.embedding_status = "ready"
            db_obj.embedding_updated_at = func.now()
            db_obj.embedding_error = None
        except EmbeddingError as e:
            db_obj.embedding = None
            db_obj.embedding_model = "local-deterministic-v1"
            db_obj.embedding_dim = None
            db_obj.embedding_version = (db_obj.embedding_version or 0) + 1
            db_obj.embedding_status = "failed"
            db_obj.embedding_updated_at = func.now()
            db_obj.embedding_error = str(e)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_incident_soft(db: Session, tenant_id: str, incident_id: int, deleted_by: str) -> Optional[IncidentLog]:
    db_obj = (
        db.query(IncidentLog)
        .filter(
            IncidentLog.tenant_id == tenant_id,
            IncidentLog.id == incident_id,
            IncidentLog.is_deleted == False,  
        )
        .first()
    )
    if not db_obj:
        return None

    db_obj.is_deleted = True
    db_obj.deleted_at = func.now()
    db_obj.deleted_by = deleted_by

    db.commit()
    db.refresh(db_obj)
    return db_obj
