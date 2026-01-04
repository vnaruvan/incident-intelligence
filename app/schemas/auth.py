# schemas/auth.py

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ApiKeyCreate(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    actor_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)  # viewer | responder | auditor | admin
    name: Optional[str] = None

class ApiKeyCreated(BaseModel):
    id: int
    tenant_id: str
    actor_id: str
    role: str
    name: Optional[str] = None
    api_key: str  # shown once

class AuditLogRead(BaseModel):
    id: int
    tenant_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    created_at: datetime
    request_meta: Optional[Any] = None
    result_ids: Optional[Any] = None
    prev_hash: Optional[str] = None
    hash: str

    model_config = ConfigDict(from_attributes=True)

