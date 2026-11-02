"""
Modèle Payment — historique des transactions et des commissions.
"""
import uuid
import enum
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_total = Column(Integer, nullable=False)      # Montant total payé par le visiteur
    platform_fee = Column(Integer, nullable=False)      # Ta commission (ex: 10%)
    organizer_amount = Column(Integer, nullable=False)  # Montant pour l'organisateur
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    transaction_id = Column(String(255), nullable=True)  # ID de transaction Stripe (mock)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relation
    registration = relationship("Registration", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment {self.id} - {self.status.value}>"
