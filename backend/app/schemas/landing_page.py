"""Schémas de la landing page publique d'un camp."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import SeasonTheme


class LandingPageUpdate(BaseModel):
    season_theme: SeasonTheme
    hero_title: str = Field(min_length=1, max_length=200)
    hero_description: str | None = Field(default=None, max_length=2000)
    # True = publier le camp ; False = le repasser en brouillon.
    publish: bool = False


class LandingPageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camp_id: UUID
    season_theme: SeasonTheme
    hero_title: str
    hero_description: str | None
    published_at: datetime | None
