import os
import sys

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole, UserStatus


def main() -> int:
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    first_name = os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", "Super").strip()
    last_name = os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", "Admin").strip()

    if not email or len(password) < 12:
        print(
            "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD "
            "(at least 12 characters).",
            file=sys.stderr,
        )
        return 2

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            if existing.role != UserRole.SUPER_ADMIN:
                print("The configured email belongs to a non-super-admin account.", file=sys.stderr)
                return 1
            print(f"Super-admin already exists: {email}")
            return 0

        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
            )
        )
        db.commit()
        print(f"Created initial super-admin: {email}")
        return 0
    except IntegrityError:
        db.rollback()
        print("Could not create the bootstrap super-admin due to a database conflict.", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())