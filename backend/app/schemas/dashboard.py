"""Schémas du tableau de bord organisateur."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CampCounts(BaseModel):
    """Nombre de camps par statut."""

    total: int
    draft: int
    published: int
    archived: int


class RegistrationCounts(BaseModel):
    total: int


class RecentRegistration(BaseModel):
    """Une inscription récente, affichée dans le tableau de bord."""

    id: UUID
    camp_id: UUID
    first_name: str
    last_name: str
    email: str
    created_at: datetime | None


class DashboardSummary(BaseModel):
    """Réponse complète de GET /api/dashboard/summary."""

    camps: CampCounts
    registrations: RegistrationCounts
    recent_registrations: list[RecentRegistration]
