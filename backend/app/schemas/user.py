"""Schémas des comptes utilisateurs."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole, UserStatus


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


class UserView(BaseModel):
    """Vue publique d'un compte : jamais de password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    status: UserStatus
