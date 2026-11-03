import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ModalityType(str, enum.Enum):
    AGE_RESTRICTION = "age_restriction"
    EDUCATION_LEVEL = "education_level"
    OTHER = "other"
    INCLUDED = "included"
    OPTION = "option"

class CampModality(Base):
    __tablename__ = "camp_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)
    type = Column(Enum(ModalityType), nullable=False)
    label = Column(String, nullable=False)

    camp = relationship("Camp", back_populates="modalities")
