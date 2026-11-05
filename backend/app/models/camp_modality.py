"""Modèle CampModality : ce qui est inclus, les options et les critères d'un camp."""
import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ModalityType(str, enum.Enum):
    """Nature de la modalité : critère d'éligibilité, élément inclus ou option."""

    AGE_RESTRICTION = "age_restriction"
    EDUCATION_LEVEL = "education_level"
    OTHER = "other"
    INCLUDED = "included"
    OPTION = "option"

class CampModality(Base):
    """Une ligne affichée sur la landing page, ex. « Repas inclus », « Niveau collège »."""

    __tablename__ = "camp_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)
    type = Column(Enum(ModalityType), nullable=False)
    label = Column(String, nullable=False)

    camp = relationship("Camp", back_populates="modalities")
