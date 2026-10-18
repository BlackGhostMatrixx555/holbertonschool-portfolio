import csv
import os
import subprocess
import tempfile
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.models import User, UserRole

router = APIRouter()


def _require_super_admin(user: User) -> None:
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")


@router.get("/admin/backups")
def export_backup(
    background_tasks: BackgroundTasks,
    format: str = Query(pattern="^(csv|sql)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(current_user)

    if format == "csv":
        archive = BytesIO()
        with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
            connection = db.connection()
            for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
                output = StringIO(newline="")
                writer = csv.writer(output)
                writer.writerow(column.name for column in table.columns)
                result = connection.execute(select(table))
                writer.writerows(result.fetchall())
                zip_file.writestr(f"{table.name}.csv", output.getvalue())
        archive.seek(0)
        return StreamingResponse(
            archive,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=camporga-backup-csv.zip"},
        )

    database_url = make_url(settings.DATABASE_URL)
    if database_url.get_backend_name() != "postgresql":
        raise HTTPException(status_code=501, detail="Les exports SQL nécessitent PostgreSQL.")

    descriptor, path = tempfile.mkstemp(prefix="camporga-backup-", suffix=".sql")
    os.close(descriptor)
    environment = os.environ.copy()
    if database_url.password is not None:
        environment["PGPASSWORD"] = database_url.password
    command = [
        "pg_dump",
        "--no-owner",
        "--no-privileges",
        "--format=plain",
        "--file",
        path,
    ]
    if database_url.host:
        command.extend(["--host", database_url.host])
    if database_url.port:
        command.extend(["--port", str(database_url.port)])
    if database_url.username:
        command.extend(["--username", database_url.username])
    command.append(database_url.database or "")
    try:
        subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        os.unlink(path)
        raise HTTPException(status_code=503, detail="La création du backup SQL a échoué.") from exc

    background_tasks.add_task(os.unlink, path)
    return FileResponse(
        path,
        media_type="application/sql",
        filename="camporga-backup.sql",
        background=background_tasks,
    )