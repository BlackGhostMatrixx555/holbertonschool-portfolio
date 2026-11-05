"""Schémas des comptes utilisateurs."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole, UserStatus

PHONE_PATTERN = r"^\+?[0-9 .-]{6,20}$"


class UserCreate(BaseModel):
    email: EmailStr
    # 12 caractères minimum : recommandation de l'ANSSI pour un mot de passe seul.
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.ORGANIZER


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    status: UserStatus


class ProfileUpdate(BaseModel):
    """Ce qu'un utilisateur peut modifier lui-même (ni son rôle, ni son statut)."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, pattern=PHONE_PATTERN)


class UserView(BaseModel):
    """Vue publique d'un compte : jamais de password_hash ni de totp_secret."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone_number: str | None = None
    role: UserRole
    status: UserStatus
    is_2fa_enabled: bool = False
