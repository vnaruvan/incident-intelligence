# tests/test_api_integration.py

from app.models.incident import IncidentLog
from app.models.auth import AuditLog


def _create_incident(client, api_key: str, message: str):
    r = client.post(
        "/api/incidents",
        headers={"X-API-Key": api_key},
        json={
            "service": "payments",
            "severity": "sev2",
            "message": message,
            "reporter": "oncall",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_create_writes_raw_redacted_and_embeds_redacted(client, db_session, bootstrap_keys):
    msg = "Latency spike. bob@example.com AKIA1234567890ABCDEF"
    data = _create_incident(client, bootstrap_keys["a_admin"], msg)

    assert data["tenant_id"] == "tenant_a"
    assert data["embedding_status"] == "ready"
    assert "[REDACTED_EMAIL]" in data["message_redacted"]
    assert "[REDACTED_AWS_KEY]" in data["message_redacted"]

    row = db_session.query(IncidentLog).filter(IncidentLog.id == data["id"]).first()
    assert row.message_raw == msg
    assert "[REDACTED_EMAIL]" in row.message_redacted
    assert row.embedding is not None


def test_search_returns_created_incident_and_writes_audit_log(client, db_session, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Payment latency spike after deploy")

    r = client.get(
        "/api/search",
        headers={"X-API-Key": bootstrap_keys["a_admin"]},
        params={"q": "payment latency spike", "top_k": 5},
    )
    assert r.status_code == 200, r.text
    ids = [x["id"] for x in r.json()]
    assert created["id"] in ids

    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == "tenant_a", AuditLog.action == "INCIDENT_SEARCH")
        .all()
    )
    assert len(logs) == 1
    assert created["id"] in logs[0].result_ids


def test_update_message_increments_embedding_version(client, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Initial message")

    g = client.get(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["a_admin"]})
    assert g.status_code == 200
    assert g.json()["embedding_version"] == 1

    u = client.patch(
        f"/api/incidents/{created['id']}",
        headers={"X-API-Key": bootstrap_keys["a_responder"]},
        json={"message": "Updated message with new context"},
    )
    assert u.status_code == 200, u.text
    assert u.json()["embedding_version"] == 2


def test_soft_delete_hides_from_read_and_search(client, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Gateway 502 spike")

    d = client.delete(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["a_admin"]})
    assert d.status_code == 200, d.text

    # read should be hidden
    g = client.get(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["a_admin"]})
    assert g.status_code == 404, g.text

    # search should not return it
    s = client.get("/api/search", headers={"X-API-Key": bootstrap_keys["a_admin"]}, params={"q": "Gateway 502", "top_k": 10})
    assert s.status_code == 200
    ids = [x["id"] for x in s.json()]
    assert created["id"] not in ids


def test_rbac_viewer_cannot_read_raw(client, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Contains raw sensitive details")

    r = client.get(f"/api/incidents/{created['id']}/raw", headers={"X-API-Key": bootstrap_keys["a_viewer"]})
    assert r.status_code in (401, 403), r.text


def test_rbac_auditor_can_read_audit_logs(client, bootstrap_keys):
    _ = _create_incident(client, bootstrap_keys["a_admin"], "Test for audit access")

    r = client.get("/api/audit-logs", headers={"X-API-Key": bootstrap_keys["a_auditor"]})
    assert r.status_code == 200, r.text


def test_rbac_only_admin_can_delete(client, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Only admin should delete this")

    r = client.delete(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["a_responder"]})
    assert r.status_code in (401, 403), r.text


def test_multi_tenant_separation(client, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Tenant A incident")

    # Tenant B should not see it
    r = client.get(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["b_admin"]})
    assert r.status_code == 404, r.text

    s = client.get("/api/search", headers={"X-API-Key": bootstrap_keys["b_admin"]}, params={"q": "Tenant A incident", "top_k": 10})
    assert s.status_code == 200
    ids = [x["id"] for x in s.json()]
    assert created["id"] not in ids


def test_audit_coverage_read_and_search(client, db_session, bootstrap_keys):
    created = _create_incident(client, bootstrap_keys["a_admin"], "Audit coverage test")

    _ = client.get(f"/api/incidents/{created['id']}", headers={"X-API-Key": bootstrap_keys["a_admin"]})
    _ = client.get("/api/search", headers={"X-API-Key": bootstrap_keys["a_admin"]}, params={"q": "Audit coverage", "top_k": 5})

    actions = [x.action for x in db_session.query(AuditLog).filter(AuditLog.tenant_id == "tenant_a").all()]
    assert "INCIDENT_READ" in actions
    assert "INCIDENT_SEARCH" in actions
