"""
Modèle Registration — les inscriptions des visiteurs à un camp.
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("camps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    comment = Column(Text)
    confirmed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    camp = relationship("Camp", back_populates="registrations")

    def __repr__(self) -> str:
        return f"<Registration {self.email} for camp {self.camp_id}>"
