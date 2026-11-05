"""Modèle Registration : inscriptions des visiteurs à un camp."""
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Registration(Base):
    """Inscription d'un visiteur à un camp (sans compte : prénom, nom, email)."""

    __tablename__ = "registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    # Enregistré en minuscules par le service : une même adresse ne peut
    # s'inscrire qu'une fois par camp, quelle que soit la casse.
    email = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    # Présence confirmée par l'organisateur (case à cocher dans l'espace organisateur).
    confirmed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    camp = relationship("Camp", back_populates="registrations")
