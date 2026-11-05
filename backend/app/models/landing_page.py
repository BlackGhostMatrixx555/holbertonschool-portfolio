import uuid
import enum
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SeasonTheme(str, enum.Enum):
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    AUTUMN = "autumn"

class LandingPage(Base):
    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False, unique=True)
    season_theme = Column(Enum(SeasonTheme), nullable=False)
    hero_title = Column(String, nullable=False)
    hero_description = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    camp = relationship("Camp", back_populates="landing_page")
