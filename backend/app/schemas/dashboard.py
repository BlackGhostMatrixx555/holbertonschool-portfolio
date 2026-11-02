"""Schémas du tableau de bord organisateur."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CampCounts(BaseModel):
    total: int
    draft: int
    published: int
    archived: int


class RegistrationCounts(BaseModel):
    total: int


class RecentRegistration(BaseModel):
    id: UUID
    camp_id: UUID
    first_name: str
    last_name: str
    email: str
    created_at: datetime | None


class DashboardSummary(BaseModel):
    camps: CampCounts
    registrations: RegistrationCounts
    recent_registrations: list[RecentRegistration]
