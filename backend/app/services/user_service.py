"""Gestion des comptes : connexion, inscription, profil, administration, suppression."""
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import create_access_token, create_two_factor_token, hash_password, verify_password
from app.models import Backup, Camp, User, UserRole, UserStatus
from app.schemas.auth import RegisterRequest
from app.schemas.user import ProfileUpdate, UserCreate


class InvalidCredentialsError(Exception):
    """Identifiants refusés (traduit en 401 par la route de connexion)."""


class PendingAccountError(Exception):
    """Mot de passe correct, mais compte pas encore validé (traduit en 403)."""


def _token_response(user: User) -> dict:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token = create_access_token(subject=user.id, expires_delta=timedelta(seconds=expires_in))
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}


def authenticate(db: Session, email: str, password: str) -> dict:
    """
    Étape 1 de la connexion : vérifie l'email et le mot de passe.

    - Même message que l'email existe ou non : on ne révèle pas quels comptes
      existent (énumération de comptes).
    - Si la 2FA est activée, on ne délivre PAS de jeton de session : seulement
      un jeton temporaire pour l'étape 2 (le code à 6 chiffres).
    """
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None or not verify_password(password, user.password_hash) or user.status == UserStatus.DISABLED:
        raise InvalidCredentialsError("Email ou mot de passe incorrect.")
    if user.status == UserStatus.INACTIVE:
        # Le mot de passe est juste : on peut expliquer pourquoi l'accès est refusé.
        raise PendingAccountError("Votre compte est en attente de validation par le super admin.")

    if user.is_2fa_enabled:
        return {"requires_2fa": True, "temp_token": create_two_factor_token(user.id)}
    return _token_response(user)


def complete_two_factor_login(user: User) -> dict:
    """Étape 2 de la connexion : le code TOTP a été vérifié par le service 2FA."""
    return _token_response(user)


def register(db: Session, payload: RegisterRequest) -> User:
    """
    Inscription publique d'un organisateur (apport de tete-work).

    Le compte est créé INACTIF avec le rôle SEM : le cahier des charges confie
    la gestion des accès au super admin, qui doit l'activer. Sans cette étape,
    n'importe qui pourrait créer des camps publics sur la plateforme.
    """
    email = payload.email.lower()
    if db.query(User.id).filter(User.email == email).first() is not None:
        raise ConflictError("Cette adresse email est déjà utilisée.")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        phone_number=payload.phone_number,
        role=UserRole.SEM,
        status=UserStatus.INACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def _get_user(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Utilisateur introuvable.")
    return user


def update_role(db: Session, user_id: UUID, role: UserRole, current_user: User) -> User:
    user = _get_user(db, user_id)
    # Garde-fou : un super admin qui se rétrograderait laisserait la plateforme
    # sans personne pour gérer les comptes.
    if user.id == current_user.id and role != UserRole.SUPER_ADMIN:
        raise ConflictError("Vous ne pouvez pas modifier votre propre rôle.")
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


def _delete(db: Session, user: User) -> None:
    """
    Supprime un compte s'il n'a plus de données rattachées.

    On refuse (409) plutôt que de supprimer en cascade : supprimer un
    organisateur effacerait sinon ses camps ET les inscriptions des familles.
    """
    if db.query(Camp.id).filter(Camp.organizer_id == user.id).first() is not None:
        raise ConflictError("Ce compte gère encore des camps : supprimez-les ou transférez-les d'abord.")
    if db.query(Backup.id).filter(Backup.triggered_by == user.id).first() is not None:
        raise ConflictError("Ce compte a réalisé des sauvegardes : il doit être conservé pour la traçabilité.")
    db.delete(user)
    db.commit()


def delete_own_account(db: Session, user: User) -> None:
    """Suppression de son propre compte (apport de tete-work)."""
    if user.role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Le compte super admin ne peut pas être supprimé.")
    _delete(db, user)


def delete_user(db: Session, user_id: UUID) -> None:
    """Suppression d'un compte par le super admin."""
    user = _get_user(db, user_id)
    if user.role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Un compte super admin ne peut pas être supprimé.")
    _delete(db, user)
