"""Route d'export des sauvegardes (super admin uniquement)."""
import os

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_super_admin
from app.db.session import get_db
from app.models import User
from app.services import backup_service

router = APIRouter(tags=["Sauvegardes"])


@router.get("/admin/backups")
def export_backup(
    background_tasks: BackgroundTasks,
    format: str = Query(pattern="^(csv|sql)$"),  # toute autre valeur -> 422
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    if format == "csv":
        return StreamingResponse(
            backup_service.export_csv_zip(db),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=camporga-backup-csv.zip"},
        )

    path = backup_service.export_sql_dump()
    # Le fichier temporaire est supprimé APRÈS l'envoi de la réponse.
    background_tasks.add_task(os.unlink, path)
    return FileResponse(path, media_type="application/sql", filename="camporga-backup.sql", background=background_tasks)
