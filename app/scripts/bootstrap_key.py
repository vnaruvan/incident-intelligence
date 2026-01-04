# app/scripts/bootstrap_key.py
import os
import secrets

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.auth import ApiKey
from app.security.hashing import sha256_hex

DEFAULT_TENANT = "demo"
DEFAULT_ACTOR = "bootstrap"
DEFAULT_ROLE = "admin"


def main() -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)

    plain = "ii_" + secrets.token_urlsafe(32)
    key_hash = sha256_hex(plain)

    with SessionLocal() as db:
        row = ApiKey(
            tenant_id=DEFAULT_TENANT,
            actor_id=DEFAULT_ACTOR,
            role=DEFAULT_ROLE,
            name="bootstrap admin",
            key_hash=key_hash,
            is_active=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

    print("\nBOOTSTRAP ADMIN KEY (save this, shown once):")
    print(plain)
    print(f"tenant_id={DEFAULT_TENANT} role={DEFAULT_ROLE} actor_id={DEFAULT_ACTOR}\n")


if __name__ == "__main__":
    main()
