# models/incident.py

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)

    tenant_id = Column(String(100), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    service = Column(String(100), index=True, nullable=True)
    severity = Column(String(20), index=True, nullable=True)

    title = Column(String(200), nullable=True)
    affected_sys = Column(Text, nullable=True)
    reporter = Column(String(100), index=True, nullable=True)
    source = Column(String(100), index=True, nullable=True)

    # Store tags as JSON array for now (simple + flexible)
    tags = Column(JSONB, nullable=True)

    # Store both. Gate raw later with RBAC.
    message_raw = Column(Text, nullable=False)
    message_redacted = Column(Text, nullable=False)

    stack_trace = Column(Text, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, server_default="false", index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(100), nullable=True)

    # Embedding + metadata
    embedding = Column(Vector(1536), nullable=True)

    embedding_model = Column(String(100), nullable=True)
    embedding_dim = Column(Integer, nullable=True)
    embedding_version = Column(Integer, nullable=True)

    # pending | ready | failed
    embedding_status = Column(String(20), nullable=False, server_default="pending", index=True)
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)
    embedding_error = Column(Text, nullable=True)

    # Useful composite indexes
    __table_args__ = (
        Index("ix_incident_logs_tenant_created", "tenant_id", "created_at"),
        Index("ix_incident_logs_tenant_service", "tenant_id", "service"),
    )

    def __repr__(self) -> str:
        return (
            f"IncidentLog(id={self.id!r}, tenant_id={self.tenant_id!r}, "
            f"created_at={self.created_at!r}, service={self.service!r}, severity={self.severity!r})"
        )
