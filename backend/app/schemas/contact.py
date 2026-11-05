"""Schémas des messages de contact (hotline)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ContactChannel, MessageStatus


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    # Longueur maximale : limite le spam et les requêtes trop lourdes.
    message: str = Field(min_length=1, max_length=2000)
    channel: ContactChannel = ContactChannel.HOTLINE


class ContactMessageStatusUpdate(BaseModel):
    status: MessageStatus


class ContactMessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camp_id: UUID
    name: str
    email: EmailStr
    message: str
    channel: ContactChannel
    status: MessageStatus
    created_at: datetime | None = None
