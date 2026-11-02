"""Gestion des comptes : connexion et administration par le super admin."""
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserStatus
from app.schemas.user import UserCreate


class InvalidCredentialsError(Exception):
    """Identifiants refusés (traduit en 401 par la route de connexion)."""


def authenticate(db: Session, email: str, password: str) -> dict:
    """
    Vérifie les identifiants et retourne un jeton d'accès.

    Le même message est renvoyé que l'email existe ou non : on ne révèle
    pas à un attaquant quels comptes existent (énumération de comptes).
    """
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if (
        user is None
        or user.status != UserStatus.ACTIVE
        or not verify_password(password, user.password_hash)
    ):
        raise InvalidCredentialsError("Email ou mot de passe incorrect.")

    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token = create_access_token(subject=user.id, expires_delta=timedelta(seconds=expires_in))
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def create_user(db: Session, payload: UserCreate) -> User:
    email = payload.email.lower()
    if db.query(User.id).filter(User.email == email).first() is not None:
        raise ConflictError("Cette adresse email est déjà utilisée.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),  # jamais le mot de passe en clair
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_user(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Utilisateur introuvable.")
    return user


def update_role(db: Session, user_id: UUID, role) -> User:
    user = _get_user(db, user_id)
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_status(db: Session, user_id: UUID, new_status: UserStatus, current_user: User) -> User:
    user = _get_user(db, user_id)
    # Garde-fou : le super admin ne doit pas pouvoir se bloquer lui-même.
    if user.id == current_user.id and new_status != UserStatus.ACTIVE:
        raise ConflictError("Vous ne pouvez pas désactiver votre propre compte.")
    user.status = new_status
    db.commit()
    db.refresh(user)
    return user
