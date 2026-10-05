"""
Modèles Camp et CampModality — la table centrale du schéma et ses critères
d'éligibilité.
"""
import uuid

from sqlalchemy import (
    Column, String, Text, Date, Integer, SmallInteger, DateTime,
    ForeignKey, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, pg_enum
from app.models.enums import CampStatus, ModalityType


class Camp(Base):
    __tablename__ = "camps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    # `slug` sert d'identifiant lisible dans l'URL publique :
    # camporga.fr/code-explorers plutôt qu'un UUID illisible.
    slug = Column(String(160), nullable=False, unique=True, index=True)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    city = Column(String(100))
    age = Column(SmallInteger)
    capacity = Column(Integer, nullable=False, default=0)
    status = Column(
        pg_enum(CampStatus, "camp_status"),
        nullable=False,
        default=CampStatus.DRAFT,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_camps_dates"),
    )

    organizer = relationship("User", back_populates="camps")
    # `cascade="all, delete-orphan"` : supprimer un camp supprime aussi ses
    # modalités, sa landing page et ses inscriptions — cohérent avec les
    # ON DELETE CASCADE définis dans le schéma SQL.
    modalities = relationship(
        "CampModality", back_populates="camp", cascade="all, delete-orphan"
    )
    landing_page = relationship(
        "LandingPage", back_populates="camp", uselist=False, cascade="all, delete-orphan"
    )
    registrations = relationship(
        "Registration", back_populates="camp", cascade="all, delete-orphan"
    )
    contact_messages = relationship("ContactMessage", back_populates="camp")

    def __repr__(self) -> str:
        return f"<Camp {self.slug}>"


class CampModality(Base):
    __tablename__ = "camp_modalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("camps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(pg_enum(ModalityType, "modality_type"), nullable=False)
    label = Column(String(255), nullable=False)

    camp = relationship("Camp", back_populates="modalities")

    def __repr__(self) -> str:
        return f"<CampModality {self.type.value}: {self.label}>"
