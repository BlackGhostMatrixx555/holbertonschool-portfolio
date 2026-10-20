"""
Routes pour les backups de base de données.

Réservé au super admin.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import User, UserRole
from app.schemas.backup import BackupCreate, BackupRead
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backups", tags=["backups"])


def get_backup_service(db: Session = Depends(get_db)) -> BackupService:
    return BackupService(db)


super_admin_only = require_role(UserRole.SUPER_ADMIN)


@router.post("", response_model=BackupRead, status_code=status.HTTP_201_CREATED)
def create_backup(
    data: BackupCreate,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(super_admin_only),
):
    """Génère un backup SQL ou CSV. Réservé au super admin."""
    try:
        backup = service.create(data.format, triggered_by=current_user)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return backup


@router.get("", response_model=list[BackupRead])
def list_backups(
    service: BackupService = Depends(get_backup_service),
    _: User = Depends(super_admin_only),
):
    """Liste tous les backups. Réservé au super admin."""
    return service.list()


@router.get("/{backup_id}/download")
def download_backup(
    backup_id: uuid.UUID,
    service: BackupService = Depends(get_backup_service),
    _: User = Depends(super_admin_only),
):
    """Télécharge un backup. Réservé au super admin."""
    backup = service.get_by_id(backup_id)
    if backup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup introuvable.",
        )

    file_path = service.get_file_path(backup)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Le fichier de backup a été supprimé du serveur.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )
