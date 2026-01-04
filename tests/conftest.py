# tests/conftest.py

import hashlib
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.core.database import get_db
from app.core.config import DATABASE_URL

from app.models.incident import Base
import app.models.incident as _incident_models  # noqa: F401
import app.models.auth as _auth_models          # noqa: F401


from app.crud.crud_auth import create_api_key


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(DATABASE_URL, pool_pre_ping=True)

    # pgvector extension (requires pgvector/pgvector image)
    with eng.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()

    # Clean between tests because app code commits
    db.execute(text("TRUNCATE TABLE audit_logs RESTART IDENTITY CASCADE;"))
    db.execute(text("TRUNCATE TABLE api_keys RESTART IDENTITY CASCADE;"))
    db.execute(text("TRUNCATE TABLE incident_logs RESTART IDENTITY CASCADE;"))
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session, monkeypatch):
    def _override_get_db():
        yield db_session

    # set override BEFORE creating the client
    fastapi_app.dependency_overrides[get_db] = _override_get_db

    # deterministic 1536-d embedding stub
    def fake_embeddings(text_in: str, model: str = "text-embedding-3-small"):
        h = hashlib.sha256(text_in.encode("utf-8")).digest()
        return [(h[i % len(h)] / 255.0) for i in range(1536)]

    import app.crud.crud as crud_module
    monkeypatch.setattr(crud_module, "generate_vector_embeddings", fake_embeddings)

    try:
        yield TestClient(fastapi_app)
    finally:
        fastapi_app.dependency_overrides.clear()



@pytest.fixture()
def bootstrap_keys(db_session):
    keys = {}
    _, keys["a_admin"] = create_api_key(db_session, tenant_id="tenant_a", actor_id="a_admin", role="admin", name="A admin")
    _, keys["a_viewer"] = create_api_key(db_session, tenant_id="tenant_a", actor_id="a_viewer", role="viewer", name="A viewer")
    _, keys["a_auditor"] = create_api_key(db_session, tenant_id="tenant_a", actor_id="a_auditor", role="auditor", name="A auditor")
    _, keys["a_responder"] = create_api_key(db_session, tenant_id="tenant_a", actor_id="a_resp", role="responder", name="A responder")

    _, keys["b_admin"] = create_api_key(db_session, tenant_id="tenant_b", actor_id="b_admin", role="admin", name="B admin")
    return keys
