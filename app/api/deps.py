from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_auth import authenticate_api_key, ActorContext

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_actor(
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> ActorContext:
    actor = authenticate_api_key(db, api_key or "")
    if not actor:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return actor
