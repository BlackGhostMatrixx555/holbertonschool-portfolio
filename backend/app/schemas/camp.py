"""Schémas des camps, de leurs modalités et de leur landing page."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import CampStatus, ModalityType, SeasonTheme


class ModalityInput(BaseModel):
    type: ModalityType
    label: str = Field(min_length=1, max_length=200)


class CampInput(BaseModel):
    """
    Données d'un camp, utilisées en création (POST) et en mise à jour (PATCH).

    Tous les champs sont optionnels pour permettre une mise à jour partielle ;
    le service vérifie que les champs obligatoires sont présents à la création.
    """

    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    city: str | None = Field(default=None, max_length=100)
    # "age" : raccourci historique qui fixe min_age = max_age.
    age: int | None = Field(default=None, ge=0, le=99)
    min_age: int | None = Field(default=None, ge=0, le=99)
    max_age: int | None = Field(default=None, ge=0, le=99)
    capacity: int | None = Field(default=None, ge=1, le=10000)
    status: CampStatus | None = None
    modalities: list[ModalityInput] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def check_consistency(self):
        """Règles qui portent sur plusieurs champs à la fois."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date doit être supérieure ou égale à start_date")
        if self.min_age is not None and self.max_age is not None and self.min_age > self.max_age:
            raise ValueError("min_age doit être inférieur ou égal à max_age")
        return self


class ModalityView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: ModalityType
    label: str


class LandingPageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season_theme: SeasonTheme
    hero_title: str
    hero_description: str | None
    published_at: datetime | None


class CampPublicView(BaseModel):
    """Ce qu'un visiteur anonyme peut voir d'un camp publié."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    start_date: date
    end_date: date
    city: str
    min_age: int
    max_age: int
    status: CampStatus
    remaining_places: int
    modalities: list[ModalityView]
    landing_page: LandingPageSummary | None


class CampView(CampPublicView):
    """Vue organisateur : ajoute les champs internes."""

    organizer_id: UUID
    capacity: int
    registrations_count: int
