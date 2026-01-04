# security/redaction.py

import re

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1}\d{3}[-.\s]?\d{4}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
AWS_ACCESS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
API_KEY_LABEL = (r"(?i)\b(api[-_ ]?key|x[-_ ]?api[-_ ]?key)\b\s*[:=]\s*[A-Za-z0-9_\-]{12,}")
JWT_RE = re.compile(r"\beyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b")
TOKEN_KV_RE = re.compile(r"(?i)\b(session\s*token|token|access\s*token|id\s*token|bearer)\b\s*[:=]\s*([A-Za-z0-9._\-]{16,})")
BEARER_RE = re.compile(r"(?i)\bAuthorization:\s*Bearer\s+([A-Za-z0-9._\-]{16,})")


def redact_text(text: str) -> str:
    if not text:
        return ""

    redacted = text
    redacted = EMAIL.sub("[REDACTED_EMAIL]", redacted)
    redacted = PHONE.sub("[REDACTED_PHONE]", redacted)
    redacted = SSN.sub("[REDACTED_SSN]", redacted)
    redacted = AWS_ACCESS_KEY.sub("[REDACTED_AWS_KEY]", redacted)
    redacted = JWT.sub("[REDACTED_JWT]", redacted)
    redacted = JWT_RE.sub("[REDACTED_JWT]", redacted)
    redacted = TOKEN_KV_RE.sub("[REDACTED_TOKEN]", redacted)
    redacted = BEARER_RE.sub("[REDACTED_BEARER]", redacted)
    redacted = CREDIT_CARD.sub("[REDACTED_PAN]", redacted)

    return redacted
