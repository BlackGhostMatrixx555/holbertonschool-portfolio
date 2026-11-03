"""Schémas du chatbot de la landing page."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # Identifiant de session généré par le navigateur (UUID) ; absent au 1er message.
    session_id: str | None = Field(default=None, min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")
    message: str = Field(min_length=1, max_length=500)


class ChatReply(BaseModel):
    session_id: str
    reply: str
    intent: str


class ChatMessage(BaseModel):
    role: Literal["visitor", "bot"]
    content: str
    intent: str | None = None
    at: datetime


class ConversationView(BaseModel):
    session_id: str
    camp_slug: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage]


class IntentCount(BaseModel):
    intent: str
    count: int


class ChatStats(BaseModel):
    conversations: int
    visitor_messages: int
    top_intents: list[IntentCount]
