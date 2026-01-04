# models/auth.py

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.incident import Base  # reuse Base from models/incident.py


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)

    actor_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False, index=True)  # viewer|responder|auditor|admin

    name = Column(String(200), nullable=True)

    # Store only a hash of the key, never the plaintext
    key_hash = Column(String(64), nullable=False, unique=True, index=True)

    is_active = Column(Boolean, nullable=False, server_default="true", index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    actor_id = Column(String(100), nullable=False, index=True)

    # examples: "INCIDENT_READ", "INCIDENT_SEARCH", "INCIDENT_CREATE", "INCIDENT_DELETE"
    action = Column(String(50), nullable=False, index=True)

    resource_type = Column(String(50), nullable=False, index=True)  # "incident"
    resource_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # store redacted query/meta, never raw secrets
    request_meta = Column(JSONB, nullable=True)
    # list of ids returned from a search, etc.
    result_ids = Column(JSONB, nullable=True)

    # tamper-evident chain per tenant
    prev_hash = Column(String(64), nullable=True)
    hash = Column(String(64), nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
    )
