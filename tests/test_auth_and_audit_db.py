# tests/test_auth_and_audit_db.py

from app.security.hashing import sha256_hex, canonical_json
from app.crud.crud_auth import create_api_key, authenticate_api_key, append_audit_log, ActorContext
from app.models.auth import ApiKey


def test_api_key_hashing_and_auth(db_session):
    row, plain = create_api_key(db_session, tenant_id="tenant_a", actor_id="admin", role="admin", name="test")

    stored = db_session.query(ApiKey).filter(ApiKey.id == row.id).first()
    assert stored.key_hash == sha256_hex(plain)
    assert stored.key_hash != plain  # never store plaintext

    ok = authenticate_api_key(db_session, plain)
    assert ok is not None
    assert ok.tenant_id == "tenant_a"
    assert ok.role == "admin"

    bad = authenticate_api_key(db_session, "wrong-key")
    assert bad is None


def test_audit_log_hash_chain(db_session):
    actor = ActorContext(tenant_id="tenant_a", actor_id="auditor", role="auditor", api_key_id=1)

    first = append_audit_log(
        db_session,
        actor=actor,
        action="INCIDENT_SEARCH",
        resource_type="incident",
        resource_id=None,
        request_meta={"query": "payment latency spike"},
        result_ids=[1, 2, 3],
    )
    second = append_audit_log(
        db_session,
        actor=actor,
        action="INCIDENT_READ",
        resource_type="incident",
        resource_id="1",
        request_meta={"include_deleted": False},
        result_ids=None,
    )

    assert second.prev_hash == first.hash

    payload = {
        "tenant_id": second.tenant_id,
        "actor_id": second.actor_id,
        "action": second.action,
        "resource_type": second.resource_type,
        "resource_id": second.resource_id,
        "created_at": second.created_at.isoformat(),
        "request_meta": second.request_meta,
        "result_ids": second.result_ids,
        "prev_hash": second.prev_hash,
    }
    recomputed = sha256_hex((second.prev_hash or "") + "|" + canonical_json(payload))
    assert recomputed == second.hash
