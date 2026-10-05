"""
Schémas Pydantic pour les camps et leurs modalités.

- `CampCreate`     : ce qu'un organisateur envoie pour créer un camp.
- `CampUpdate`     : ce qu'il envoie pour modifier un camp (tous champs optionnels).
- `CampRead`       : ce que l'API renvoie pour un camp (version admin/organisateur).
- `CampPublicRead` : ce que l'API renvoie publiquement (via le slug), avec la landing page.
- `ModalityCreate` / `ModalityRead` : les critères d'éligibilité associés.

Note : les dates sont validées par un `@model_validator` pour garantir que
`end_date >= start_date` AVANT d'atteindre la base. Sans ça, la CheckConstraint
PostgreSQL renverrait une erreur 500 opaque au lieu d'un 422 clair.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CampStatus, ModalityType, SeasonTheme


# ---------------------------------------------------------------------------
# Modalités (critères d'éligibilité)
# ---------------------------------------------------------------------------
class ModalityCreate(BaseModel):
    """Une modalité envoyée à la création d'un camp."""

    type: ModalityType
    label: str = Field(..., min_length=1, max_length=255)


class ModalityRead(BaseModel):
    """Une modalité telle que renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: ModalityType
    label: str


# ---------------------------------------------------------------------------
# Camp — création
# ---------------------------------------------------------------------------
class CampCreate(BaseModel):
    """Données requises pour créer un camp."""

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
        """Vérifie que `end_date >= start_date` avant d'envoyer en base.

        Sans ce validateur, la contrainte CHECK de PostgreSQL se déclenche
        et FastAPI renvoie un 500 Internal Server Error opaque. Ici, on
        lève une ValueError qui sera convertie en 422 Validation Error par
        FastAPI, avec un message clair.
        """
        if self.end_date < self.start_date:
            raise ValueError("end_date doit être supérieure ou égale à start_date")
        return self


# ---------------------------------------------------------------------------
# Camp — mise à jour (tous les champs sont optionnels)
# ---------------------------------------------------------------------------
class CampUpdate(BaseModel):
    """Champs modifiables d'un camp. Tout est optionnel : on ne modifie que
    ce qui est envoyé."""

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
        """Vérifie la cohérence des dates SI les deux sont fournies.

        On ne peut valider que si `start_date` ET `end_date` sont dans la
        requête. Si une seule des deux est fournie, la validation se fera
        au niveau du service (en comparant avec les valeurs existantes).
        """
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date doit être supérieure ou égale à start_date")
        return self


# ---------------------------------------------------------------------------
# Landing page (lecture seule pour l'instant)
# ---------------------------------------------------------------------------
class LandingPageRead(BaseModel):
    """Landing page telle que renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_theme: SeasonTheme
    hero_title: str | None
    hero_description: str | None
    published_at: datetime | None


# ---------------------------------------------------------------------------
# Camp — lecture (admin / organisateur)
# ---------------------------------------------------------------------------
class CampRead(BaseModel):
    """Camp tel que renvoyé à un organisateur ou au super admin."""

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


# ---------------------------------------------------------------------------
# Camp — lecture publique (via le slug)
# ---------------------------------------------------------------------------
class CampPublicRead(BaseModel):
    """Vue publique d'un camp, exposée sur la landing page.

    On n'y met volontairement pas `organizer_id` ni `capacity` : ces
    informations ne concernent pas le visiteur.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    start_date: date
    end_date: date
    city: str | None
    age: int | None
    status: CampStatus
    modalities: list[ModalityRead] = Field(default_factory=list)
    landing_page: LandingPageRead | None = None
