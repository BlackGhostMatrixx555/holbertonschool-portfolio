"""
Création du premier super admin (script d'initialisation).

Usage : docker compose exec backend python -m scripts.bootstrap_admin
(avec BOOTSTRAP_ADMIN_EMAIL et BOOTSTRAP_ADMIN_PASSWORD définis dans le .env).
"""
import os
import sys

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole, UserStatus


def main() -> int:
    """Crée le super admin s'il n'existe pas. Code de retour 0 = succès."""
    # Identifiants lus dans l'environnement (.env) : jamais écrits dans le code.
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    first_name = os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", "Super").strip()
    last_name = os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", "Admin").strip()

    # Même règle que l'API : 12 caractères minimum.
    if not email or len(password) < 12:
        print(
            "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD "
            "(at least 12 characters).",
            file=sys.stderr,
        )
        return 2

    db = SessionLocal()
    try:
        # Script idempotent : le relancer ne crée pas de doublon.
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