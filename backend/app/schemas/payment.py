"""
Schémas Pydantic pour les paiements.
"""
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    """Données envoyées pour déclencher un paiement."""
    registration_id: uuid.UUID


class PaymentRead(BaseModel):
    """Paiement tel que renvoyé par l'API."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    registration_id: uuid.UUID
    amount_total: int
    platform_fee: int
    organizer_amount: int
    status: PaymentStatus
    transaction_id: str | None
