"""Schémas des inscriptions aux camps."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistrationCreate(BaseModel):
    """Formulaire public d'inscription (cahier des charges, module 4.4)."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    comment: str | None = Field(default=None, max_length=1000)


class AttendanceUpdate(BaseModel):
    confirmed: bool


class RegistrationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camp_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    comment: str | None
    confirmed: bool
    created_at: datetime | None = None
