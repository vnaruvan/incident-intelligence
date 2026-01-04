import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.crud_auth import create_api_key

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def main():
    db = SessionLocal()
    try:
        seeds = [
            # tenant, actor_id, role, name
            ("demo", "admin_demo", "admin", "Demo Admin"),
            ("demo", "auditor_demo", "auditor", "Demo Auditor"),
            ("demo", "viewer_demo", "viewer", "Demo Viewer"),
            ("acme", "admin_acme", "admin", "Acme Admin"),
            ("acme", "viewer_acme", "viewer", "Acme Viewer"),
        ]

        print("\n== BOOTSTRAPPED API KEYS (copy these; plaintext shown only once) ==")
        for tenant_id, actor_id, role, name in seeds:
            row, plain = create_api_key(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                role=role,
                name=name,
            )
            print(f"{tenant_id:5} | {role:7} | {actor_id:12} | {plain}")

        print("\nDone.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
