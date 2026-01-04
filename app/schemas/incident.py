# schemas/incident.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class IncidentLogCreate(BaseModel):
    service: str
    severity: str

    title: Optional[str] = None
    affected_sys: Optional[str] = None
    reporter: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None

    message: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None


class UpdateIncident(BaseModel):
    service: Optional[str] = None
    severity: Optional[str] = None

    title: Optional[str] = None
    affected_sys: Optional[str] = None
    reporter: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None

    message: Optional[str] = None
    stack_trace: Optional[str] = None


class IncidentLogRead(BaseModel):
    id: int
    tenant_id: str

    created_at: datetime
    updated_at: datetime

    service: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    affected_sys: Optional[str] = None
    reporter: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None

    message_redacted: str
    stack_trace: Optional[str] = None

    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None
    embedding_version: Optional[int] = None
    embedding_status: str
    embedding_updated_at: Optional[datetime] = None
    embedding_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class IncidentRawRead(BaseModel):
    id: int
    tenant_id: str
    message_raw: str

    model_config = ConfigDict(from_attributes=True)

