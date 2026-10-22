"""
Schémas Pydantic pour les inscriptions.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import DevEmailStr as EmailStr


class RegistrationCreate(BaseModel):
    """Données envoyées par un visiteur pour s'inscrire à un camp."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    comment: str | None = None
    confirmed: bool = False


class RegistrationRead(BaseModel):
    """Inscription telle que renvoyée par l'API (vue admin/organisateur)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camp_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    comment: str | None
    confirmed: bool
    created_at: datetime
