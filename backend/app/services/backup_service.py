"""
Sauvegardes de la base, réservées au super admin.

Fusion des deux versions :
- génération : celle de collins (CSV en mémoire, pg_dump appelé sans shell) ;
- historique : celui de tete-work (chaque export est écrit dans BACKUP_DIR et
  tracé dans la table `backups`, puis retéléchargeable).

Formats :
- CSV : une archive ZIP contenant un fichier CSV par table.
- SQL : un dump complet produit par l'outil officiel pg_dump.
"""
import csv
import os
import subprocess
import uuid
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ServiceUnavailableError
from app.db.base_class import Base
from app.models import Backup, BackupFormat, User


def backup_dir() -> Path:
    path = Path(settings.BACKUP_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_csv_zip(db: Session, target: Path) -> None:
    with ZipFile(target, "w", ZIP_DEFLATED) as zip_file:
        connection = db.connection()
        for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
            output = StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow(column.name for column in table.columns)  # en-têtes
            writer.writerows(connection.execute(select(table)).fetchall())
            zip_file.writestr(f"{table.name}.csv", output.getvalue())


def _write_sql_dump(target: Path) -> None:
    """
    Lance pg_dump vers `target`.

    Sécurité : la commande est passée sous forme de liste (pas de shell),
    ce qui empêche toute injection de commande ; le mot de passe passe par
    la variable PGPASSWORD et n'apparaît pas dans la ligne de commande.
    """
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        error = AppError("Les exports SQL nécessitent PostgreSQL.")
        error.status_code = 501
        raise error

    environment = os.environ.copy()
    if url.password is not None:
        environment["PGPASSWORD"] = url.password

    command = ["pg_dump", "--no-owner", "--no-privileges", "--format=plain", "--file", str(target)]
    if url.host:
        command += ["--host", url.host]
    if url.port:
        command += ["--port", str(url.port)]
    if url.username:
        command += ["--username", url.username]
    command.append(url.database or "")

    try:
        subprocess.run(command, env=environment, check=True, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        target.unlink(missing_ok=True)
        raise ServiceUnavailableError("La création du backup SQL a échoué.") from exc


def create(db: Session, backup_format: BackupFormat, user: User) -> Backup:
    """Génère le fichier, puis enregistre l'export dans l'historique."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = uuid.uuid4()
    extension = "sql" if backup_format == BackupFormat.SQL else "zip"
    target = backup_dir() / f"camporga_{timestamp}_{backup_id.hex[:8]}.{extension}"

    if backup_format == BackupFormat.SQL:
        _write_sql_dump(target)
    else:
        _write_csv_zip(db, target)

    backup = Backup(
        id=backup_id,
        format=backup_format,
        triggered_by=user.id,
        file_path=str(target),
        file_size_kb=max(1, target.stat().st_size // 1024),
    )
    db.add(backup)
    db.commit()
    db.refresh(backup)
    return backup


def list_backups(db: Session) -> list[Backup]:
    return db.query(Backup).order_by(Backup.created_at.desc()).all()


def get_file(db: Session, backup_id: UUID) -> Path:
    backup = db.get(Backup, backup_id)
    if backup is None:
        raise NotFoundError("Sauvegarde introuvable.")
    path = Path(backup.file_path).resolve()
    # Défense en profondeur : on ne sert que des fichiers du dossier des sauvegardes.
    if backup_dir().resolve() not in path.parents or not path.exists():
        error = AppError("Le fichier de cette sauvegarde n'existe plus sur le serveur.")
        error.status_code = 410
        raise error
    return path
