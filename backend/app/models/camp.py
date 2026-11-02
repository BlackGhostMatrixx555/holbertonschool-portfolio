"""
Modèle Camp : la table centrale de CampOrga.

Un camp appartient à un organisateur (users) et regroupe ses modalités,
sa landing page, ses inscriptions et ses messages de contact.
cascade="all, delete-orphan" : supprimer un camp supprime aussi tout ce
qui en dépend, sans laisser de lignes orphelines.
"""
import enum
import uuid

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class CampStatus(str, enum.Enum):
    DRAFT = "draft"          # en préparation, invisible du public
    PUBLISHED = "published"  # visible, inscriptions ouvertes
    ARCHIVED = "archived"    # terminé, conservé pour l'historique


class Camp(Base):
    __tablename__ = "camps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    # Le slug sert d'URL publique (ex. /camps/code-explorers-ete-2026) ;
    # l'index unique garantit qu'il n'y a pas deux camps à la même adresse.
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    city = Column(String, nullable=False)
    min_age = Column(SmallInteger, nullable=False)
    max_age = Column(SmallInteger, nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(CampStatus), default=CampStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organizer = relationship("User", back_populates="camps")
    registrations = relationship("Registration", back_populates="camp", cascade="all, delete-orphan")
    modalities = relationship("CampModality", back_populates="camp", cascade="all, delete-orphan")
    landing_page = relationship("LandingPage", back_populates="camp", uselist=False, cascade="all, delete-orphan")
    messages = relationship("ContactMessage", back_populates="camp", cascade="all, delete-orphan")

    @property
    def registrations_count(self) -> int:
        """Nombre d'inscrits (calculé, non stocké : toujours à jour)."""
        return len(self.registrations)

    @property
    def remaining_places(self) -> int:
        """Places restantes affichées sur la landing page."""
        return max(self.capacity - self.registrations_count, 0)

    def __repr__(self):
        return f"<Camp id={self.id!r} name={self.name!r}>"
