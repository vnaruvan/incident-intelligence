# Incident Intelligence

Incident Intelligence is a small, production-minded incident log service that prioritizes three things:

1. Safe storage of incident text with redaction
2. Search that still works when external embedding providers are unavailable
3. Auditability via a tamper-evident per-tenant audit chain

It exposes a FastAPI REST API, stores data in Postgres, and uses pgvector for similarity search.

## Why this exists

Most incident tools either store raw JSON blobs with weak governance, or they bolt on “AI search” in a way that breaks the moment the embedding provider rate limits. This project is built to be reviewable in a clean local clone and to keep its core features functioning at $0.

## Core features

- Multi-tenant incident storage with explicit fields (not JSON-only)
- Redaction pipeline for message text (emails, PANs, tokens, etc.)
- RBAC via API keys (viewer, responder, auditor, admin)
- Semantic search via pgvector
- Deterministic local embeddings mode for offline, zero-cost demo
- Audit log with a per-tenant hash chain (tamper-evident)
- Health and readiness endpoints (`/health`, `/ready`)
- Lightweight demo UI (`/ui`) and API docs (`/docs`, `/redoc`)

## Architecture

flowchart TB
  client["Client (UI or curl)"] -->|"X-API-Key"| api["FastAPI"]
  api --> auth["Auth + RBAC"]
  auth --> routes["Routes (/api/*)"]

  routes --> redact["Redaction"]
  routes --> embed["Embeddings (local or external)"]

  redact --> incidents["Postgres: incident_logs"]
  embed --> incidents

  routes --> search["pgvector similarity search"]
  search --> incidents

  routes --> audit["Audit append (hash chain)"]
  audit --> auditlog["Postgres: audit_logs"]

  api --> health["GET /health"]
  api --> ready["GET /ready"]
  ready --> dbcheck["DB check"]
  dbcheck --> incidents


## Request path in practice

1. Client sends request with `X-API-Key`
2. API authenticates key, derives `tenant_id` and role
3. Payload is validated, message is redacted
4. Incident is inserted
5. An embedding is generated
6. Local deterministic mode is default for demos
7. External provider can be enabled via environment
8. Audit log entry is appended with a chained hash per tenant

---

## Tech stack

- FastAPI
- SQLAlchemy
- Alembic migrations
- Postgres 16
- pgvector extension
- Docker Compose for local DB

---

## Data model (high level)

### `incident_logs`

- `tenant_id`, `service`, `severity`, `title`, `tags`
- `message_raw`, `message_redacted`
- `embedding`, `embedding_model`, `embedding_dim`, `embedding_status`
- soft delete fields

### `api_keys`

- `tenant_id`, `actor_id`, `role`
- `key_hash`, `is_active`

### `audit_logs`

- `tenant_id`, `actor_id`, `action`, `resource_type`, `resource_id`
- `request_meta`, `result_ids`
- `prev_hash`, `hash`

---

## Local quickstart

### Prereqs

- Python 3.12
- Docker Desktop with WSL integration enabled
- `jq` (optional, but useful)

### 1) Start Postgres (pgvector image)

```bash
docker compose up -d db
docker compose ps


