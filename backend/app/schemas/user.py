"""
Schémas Pydantic pour les utilisateurs.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole, UserStatus
from app.schemas.types import DevEmailStr as EmailStr


class UserCreate(BaseModel):
    """Données pour créer un utilisateur (super admin uniquement)."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole


class UserRead(BaseModel):
    """Utilisateur tel que renvoyé par l'API.

    ⚠️ On n'expose JAMAIS `password_hash`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    created_at: datetime
