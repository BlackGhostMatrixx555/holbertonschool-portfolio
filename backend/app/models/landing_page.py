"""
Modèle LandingPage — la page publique associée à un camp (relation 1-1).
"""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, pg_enum
from app.models.enums import SeasonTheme


class LandingPage(Base):
    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # `unique=True` sur la clé étrangère : c'est ce qui garantit la relation
    # 1-1 (un camp ne peut avoir qu'une seule landing page).
    camp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("camps.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    season_theme = Column(
        pg_enum(SeasonTheme, "season_theme"),
        nullable=False,
        default=SeasonTheme.ETE,
    )
    hero_title = Column(String(200))
    hero_description = Column(Text)
    published_at = Column(DateTime(timezone=True))

    camp = relationship("Camp", back_populates="landing_page")

    def __repr__(self) -> str:
        return f"<LandingPage camp={self.camp_id} theme={self.season_theme.value}>"
