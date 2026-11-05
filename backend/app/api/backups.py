"""Routes des sauvegardes (super admin uniquement) : créer, lister, télécharger."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import require_super_admin
from app.db.session import get_db
from app.models import User
from app.schemas.backup import BackupCreate, BackupView
from app.services import backup_service

router = APIRouter(prefix="/backups", tags=["Sauvegardes"])


@router.post("", response_model=BackupView, status_code=status.HTTP_201_CREATED)
def create_backup(payload: BackupCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    """Lance un export SQL ou CSV et l'ajoute à l'historique."""
    return backup_service.create(db, payload.format, current_user)


@router.get("", response_model=list[BackupView])
def list_backups(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    """Historique des sauvegardes, la plus récente en premier."""
    return backup_service.list_backups(db)


@router.get("/{backup_id}/download")
def download_backup(backup_id: UUID, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    """Renvoie le fichier. Le nom réel est exposé au navigateur via Content-Disposition (CORS)."""
    path = backup_service.get_file(db, backup_id)
    media_type = "application/sql" if path.suffix == ".sql" else "application/zip"
    return FileResponse(path, media_type=media_type, filename=path.name)
