"""
Schémas Pydantic pour les camps et leurs modalités.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CampStatus, ModalityType, SeasonTheme


class ModalityCreate(BaseModel):
    type: ModalityType
    label: str = Field(..., min_length=1, max_length=255)


class ModalityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: ModalityType
    label: str


class CampCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    start_date: date
    end_date: date
    city: str | None = Field(None, max_length=100)
    age: int | None = Field(None, ge=0, le=120)
    capacity: int = Field(0, ge=0)
    status: CampStatus = CampStatus.DRAFT
    modalities: list[ModalityCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date doit être supérieure ou égale à start_date")
        return self


class CampUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    city: str | None = Field(None, max_length=100)
    age: int | None = Field(None, ge=0, le=120)
    capacity: int | None = Field(None, ge=0)
    status: CampStatus | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date doit être supérieure ou égale à start_date")
        return self


class LandingPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    season_theme: SeasonTheme
    hero_title: str | None
    hero_description: str | None
    published_at: datetime | None


class CampRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organizer_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    start_date: date
    end_date: date
    city: str | None
    age: int | None
    capacity: int
    status: CampStatus
    created_at: datetime
    modalities: list[ModalityRead] = Field(default_factory=list)


class CampPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    start_date: date
    end_date: date
    city: str | None
    age: int | None
    capacity: int  # <-- Ajouté pour que le frontend puisse afficher "X/Y places"
    status: CampStatus
    modalities: list[ModalityRead] = Field(default_factory=list)
    landing_page: LandingPageRead | None = None
    registration_count: int = 0  # <-- Ajouté pour le compteur d'inscrits
