"""Schémas de l'historique des sauvegardes."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import BackupFormat


class BackupCreate(BaseModel):
    format: BackupFormat


class BackupView(BaseModel):
    """Une sauvegarde de l'historique (le chemin sur le serveur n'est pas exposé)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    format: BackupFormat
    triggered_by: UUID
    file_size_kb: int | None
    created_at: datetime | None
