# tests/test_unit_security.py

import pytest
from app.security.redaction import redact_text
from app.security.hashing import sha256_hex
from app.crud.crud_auth import require_role, ActorContext
from fastapi import HTTPException

def test_redact_text_replaces_pii_and_secrets():
    text = (
        "Email bob@example.com "
        "Phone 415-555-1234 "
        "SSN 123-45-6789 "
        "AWS AKIA1234567890ABCDEF "
        "JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
    )
    red = redact_text(text)

    assert "bob@example.com" not in red
    assert "415-555-1234" not in red
    assert "123-45-6789" not in red
    assert "AKIA1234567890ABCDEF" not in red
    assert "eyJhbGci" not in red

    assert "[REDACTED_EMAIL]" in red
    assert "[REDACTED_PHONE]" in red
    assert "[REDACTED_SSN]" in red
    assert "[REDACTED_AWS_KEY]" in red
    assert "[REDACTED_JWT]" in red


def test_sha256_hex_stable():
    a = sha256_hex("hello")
    b = sha256_hex("hello")
    c = sha256_hex("hello2")

    assert a == b
    assert a != c
    assert len(a) == 64


def test_require_role_allows_and_denies():
    actor = ActorContext(tenant_id="tenant_a", actor_id="u1", role="viewer", api_key_id=1)

    require_role(actor, {"viewer", "admin"})  # allowed

    with pytest.raises(HTTPException) as e:
        require_role(actor, {"admin"})

    assert e.value.status_code == 403