import os
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.crud import create_incident
from app.schemas.incident import IncidentLogCreate

DATABASE_URL = os.environ["DATABASE_URL"]

TENANTS = ["demo", "acme"]

SERVICES = [
    "payments", "auth", "search", "notifications", "billing",
    "orders", "inventory", "shipping", "web", "ml-inference"
]

SEVERITIES = ["low", "medium", "high", "critical"]

SOURCES = ["api", "scheduler", "kafka-consumer", "webhook", "cron", "oncall-bot"]
REPORTERS = ["oncall", "sre", "backend", "platform", "pagerduty"]

TEMPLATES = [
    ("DB timeout spike", "Timeout to postgres at 10.0.0.12. User email: test@example.com."),
    ("Elevated 5xx", "Spike in 500 responses. Trace id: abc123. Contact: +1 (555) 123-4567"),
    ("Queue lag", "Kafka consumer lag rising. Topic=payments.events. AWS key: AKIAxxxxxxxxxxxxxxx"),
    ("Cache miss storm", "Redis hit rate dropped. Session token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx"),
    ("CPU saturation", "Node CPU > 95%. Instance i-1234567890abcdef0. Card 4111 1111 1111 1111"),
    ("OOM killed", "Container OOMKilled. Pod=api-7c9f. Possible leak in serializer."),
    ("Auth failures", "401 rate increased. Suspected credential stuffing from 203.0.113.10."),
    ("Latency regression", "p95 latency up after deploy v2026.01.02. Rollback initiated."),
]

TAG_POOL = ["db", "timeout", "latency", "deploy", "kafka", "redis", "auth", "5xx", "capacity", "oom", "security"]

def random_tags():
    k = random.randint(1, 3)
    return random.sample(TAG_POOL, k)

def main():
    random.seed(7)  
    n_per_tenant = int(os.environ.get("SEED_N_PER_TENANT", "60"))
    days_back = int(os.environ.get("SEED_DAYS_BACK", "14"))

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        created = 0
        now = datetime.now(timezone.utc)

        for tenant in TENANTS:
            for _ in range(n_per_tenant):
                title, base_msg = random.choice(TEMPLATES)
                svc = random.choice(SERVICES)
                sev = random.choice(SEVERITIES)
                src = random.choice(SOURCES)
                rep = random.choice(REPORTERS)

      
                created_at = now - timedelta(days=random.random() * days_back)

                payload = IncidentLogCreate(
                    service=svc,
                    severity=sev,
                    title=title,
                    affected_sys=random.choice([None, "postgres", "redis", "kafka", "nginx", "k8s-node"]),
                    reporter=rep,
                    source=src,
                    tags=random_tags(),
                    message=f"{base_msg} tenant={tenant} service={svc} sev={sev}",
                    stack_trace=None if random.random() < 0.75 else "Traceback (most recent call last): ...",
                )

                obj = create_incident(db, tenant_id=tenant, incident=payload)

                try:
                    obj.created_at = created_at
                    obj.updated_at = created_at
                    db.commit()
                except Exception:
                    db.rollback()

                created += 1

        print(f"Seeded {created} incidents total ({n_per_tenant} per tenant).")
    finally:
        db.close()

if __name__ == "__main__":
    main()
