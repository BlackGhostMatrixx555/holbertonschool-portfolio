"""
Schémas Pydantic pour les backups.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import BackupFormat


class BackupCreate(BaseModel):
    """Données envoyées pour déclencher un backup."""

    format: BackupFormat


class BackupRead(BaseModel):
    """Backup tel que renvoyé par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    format: BackupFormat
    triggered_by: uuid.UUID
    file_path: str
    file_size_kb: int | None
    created_at: datetime
