#!/usr/bin/env bash
set -euo pipefail

docker compose up -d db

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://postgres:postgres@localhost:5432/incident_intel}"

docker compose exec -T db createdb -U postgres incident_intel || true
docker compose exec -T db psql -U postgres -d incident_intel -c "CREATE EXTENSION IF NOT EXISTS vector;"

alembic upgrade head

python -m app.scripts.bootstrap_demo_keys
python -m app.scripts.seed_incidents --n 120

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
