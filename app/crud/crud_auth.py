# crud_auth.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict
import secrets

from sqlalchemy.orm import Session

from app.models.auth import ApiKey, AuditLog
from app.security.hashing import sha256_hex, canonical_json
from app.security.redaction import redact_text
from fastapi import HTTPException


VALID_ROLES = {"viewer", "responder", "auditor", "admin"}


@dataclass(frozen=True)
class ActorContext:
    tenant_id: str
    actor_id: str
    role: str
    api_key_id: int

def create_api_key(db: Session, tenant_id: str, actor_id: str, role: str, name: Optional[str] = None) -> tuple[ApiKey, str]:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")

    api_key_plain = secrets.token_urlsafe(32)
    key_hash = sha256_hex(api_key_plain)

    row = ApiKey(
        tenant_id=tenant_id,
        actor_id=actor_id,
        role=role,
        name=name,
        key_hash=key_hash,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, api_key_plain


def authenticate_api_key(db: Session, api_key_plain: str) -> Optional[ActorContext]:
    if not api_key_plain or not api_key_plain.strip():
        return None

    key_hash = sha256_hex(api_key_plain.strip())
    row = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()  # noqa: E712
    if not row:
        return None
    return ActorContext(tenant_id=row.tenant_id, actor_id=row.actor_id, role=row.role, api_key_id=row.id)


def require_role(actor: ActorContext, allowed: set[str]) -> None:
    if actor.role not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Role {actor.role} not permitted"
        )


def append_audit_log(
    db: Session,
    actor: ActorContext,
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    request_meta: Optional[Dict[str, Any]] = None,
    result_ids: Optional[List[Any]] = None,
) -> AuditLog:
    """
    Tamper-evident per-tenant hash chain:
    hash = sha256(prev_hash + "|" + canonical_json(payload))
    """
    # Always redact any free-text fields you might store
    safe_meta = request_meta or {}
    if "query" in safe_meta:
        safe_meta["query"] = redact_text(str(safe_meta["query"]))

    prev = (
        db.query(AuditLog)
        .filter(AuditLog.tenant_id == actor.tenant_id)
        .order_by(AuditLog.id.desc())
        .first()
    )
    prev_hash = prev.hash if prev else None

    created_at = datetime.now(timezone.utc)

    payload = {
        "tenant_id": actor.tenant_id,
        "actor_id": actor.actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "created_at": created_at.isoformat(),
        "request_meta": safe_meta,
        "result_ids": result_ids,
        "prev_hash": prev_hash,
    }

    h = sha256_hex((prev_hash or "") + "|" + canonical_json(payload))

    row = AuditLog(
        tenant_id=actor.tenant_id,
        actor_id=actor.actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        created_at=created_at,
        request_meta=safe_meta,
        result_ids=result_ids,
        prev_hash=prev_hash,
        hash=h,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
