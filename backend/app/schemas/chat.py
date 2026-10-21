"""
Schémas Pydantic pour le chatbot et la hotline.
"""
import uuid
from pydantic import BaseModel, Field
from app.models.enums import ContactChannel

class ChatRequest(BaseModel):
    """Message envoyé par un visiteur au chatbot."""
    message: str = Field(..., min_length=1, max_length=1000)
    camp_id: uuid.UUID | None = None

class ChatResponse(BaseModel):
    """Réponse renvoyée par le chatbot."""
    reply: str
    channel: ContactChannel = ContactChannel.CHATBOT

class ContactMessageCreate(BaseModel):
    """Message envoyé via le formulaire de contact (hotline)."""
    name: str = Field(..., min_length=1, max_length=150)
    email: str = Field(..., max_length=255)
    message: str = Field(..., min_length=1)
    camp_id: uuid.UUID | None = None
