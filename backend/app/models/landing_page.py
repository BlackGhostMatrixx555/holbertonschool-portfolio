"""Modèle LandingPage : la page publique associée à chaque camp."""
import uuid
import enum
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SeasonTheme(str, enum.Enum):
    """Thème visuel de la page (couleurs et illustrations côté front-end)."""

    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    AUTUMN = "autumn"

class LandingPage(Base):
    """Page publique d'un camp. Relation 1-1 : un seul enregistrement par camp."""

    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # unique=True garantit la relation 1-1 au niveau de la base de données.
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False, unique=True)
    season_theme = Column(Enum(SeasonTheme), nullable=False)
    hero_title = Column(String, nullable=False)
    hero_description = Column(Text, nullable=True)
    # Date de première publication ; None = page non publiée (camp en brouillon).
    published_at = Column(DateTime(timezone=True), nullable=True)

    camp = relationship("Camp", back_populates="landing_page")
