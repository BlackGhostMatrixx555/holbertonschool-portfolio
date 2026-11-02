"""
Export de sauvegarde de la base, réservé au super admin.

- CSV : une archive ZIP contenant un fichier CSV par table.
- SQL : un dump complet produit par l'outil officiel pg_dump.
"""
import csv
import os
import subprocess
import tempfile
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, ServiceUnavailableError
from app.db.base_class import Base


def export_csv_zip(db: Session) -> BytesIO:
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        connection = db.connection()
        for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
            output = StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow(column.name for column in table.columns)  # en-têtes
            writer.writerows(connection.execute(select(table)).fetchall())
            zip_file.writestr(f"{table.name}.csv", output.getvalue())
    archive.seek(0)
    return archive


def export_sql_dump() -> str:
    """
    Lance pg_dump et retourne le chemin du fichier .sql temporaire.

    Sécurité : la commande est passée sous forme de liste (pas de shell),
    ce qui empêche toute injection de commande ; le mot de passe passe par
    la variable PGPASSWORD et n'apparaît pas dans la ligne de commande.
    """
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        error = AppError("Les exports SQL nécessitent PostgreSQL.")
        error.status_code = 501
        raise error

    descriptor, path = tempfile.mkstemp(prefix="camporga-backup-", suffix=".sql")
    os.close(descriptor)

    environment = os.environ.copy()
    if url.password is not None:
        environment["PGPASSWORD"] = url.password

    command = ["pg_dump", "--no-owner", "--no-privileges", "--format=plain", "--file", path]
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
        os.unlink(path)
        raise ServiceUnavailableError("La création du backup SQL a échoué.") from exc
    return path
