"""
Service métier pour les backups.

Deux formats supportés :
  - SQL : dump complet via `pg_dump`, idéal pour restaurer la base.
  - CSV : un fichier .csv par table, zippé dans un .zip, idéal pour Excel.

Chaque backup est :
  1. Généré dans un répertoire `backend/backups/`.
  2. Enregistré en base (table `backups`) avec son format, sa taille,
     et l'utilisateur qui l'a déclenché.
"""
import csv
import io
import os
import subprocess
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Backup, BackupFormat, User


# Répertoire où sont stockés les backups.
BACKUP_DIR = Path("/app/backups")
BACKUP_DIR.mkdir(exist_ok=True, parents=True)


class BackupService:
    """Regroupe les opérations métier sur les backups."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def create(self, format: BackupFormat, triggered_by: User) -> Backup:
        """Génère un backup au format demandé et l'enregistre en base."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = uuid.uuid4()
        filename = f"backup_{timestamp}_{backup_id.hex[:8]}.{format.value}"
        file_path = BACKUP_DIR / filename

        if format == BackupFormat.SQL:
            self._export_sql(file_path)
        elif format == BackupFormat.CSV:
            self._export_csv(file_path)
        else:
            raise ValueError(f"Unsupported backup format: {format}")

        # Taille du fichier en Ko
        file_size_kb = max(1, file_path.stat().st_size // 1024)

        # Enregistrement en base
        backup = Backup(
            id=backup_id,
            format=format,
            triggered_by=triggered_by.id,
            file_path=str(file_path),
            file_size_kb=file_size_kb,
        )
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)
        return backup

    def list(self) -> list[Backup]:
        """Liste tous les backups, du plus récent au plus ancien."""
        return self.db.query(Backup).order_by(Backup.created_at.desc()).all()

    def get_by_id(self, backup_id: uuid.UUID) -> Backup | None:
        """Récupère un backup par son UUID."""
        return self.db.query(Backup).filter(Backup.id == backup_id).first()

    def get_file_path(self, backup: Backup) -> Path:
        """Récupère le chemin physique d'un backup."""
        return Path(backup.file_path)

    # ------------------------------------------------------------------
    # Export SQL (via pg_dump)
    # ------------------------------------------------------------------
    def _export_sql(self, file_path: Path) -> None:
        """Génère un dump SQL complet via `pg_dump`."""
        db_url = settings.database_url
        if not db_url.startswith("postgresql://"):
            raise ValueError(f"Unsupported DATABASE_URL: {db_url}")

        # pg_dump utilise PGPASSWORD pour ne pas demander le mot de passe
        env = os.environ.copy()
        env["PGPASSWORD"] = self._extract_password(db_url)

        try:
            result = subprocess.run(
                ["pg_dump", "--no-password", "--format=plain", "--no-owner",
                 "--no-acl", db_url],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "pg_dump not found. Install postgresql-client in the backend "
                "container (see backend/Dockerfile)."
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"pg_dump failed (exit {result.returncode}): {result.stderr}"
            )

        file_path.write_text(result.stdout, encoding="utf-8")

    def _extract_password(self, db_url: str) -> str:
        """Extrait le mot de passe depuis l'URL de connexion."""
        try:
            auth_part = db_url.split("://")[1].split("@")[0]
            return auth_part.split(":")[1]
        except IndexError:
            return ""

    # ------------------------------------------------------------------
    # Export CSV (un fichier par table, zippé)
    # ------------------------------------------------------------------
    def _export_csv(self, file_path: Path) -> None:
        """Génère un ZIP contenant un fichier CSV par table."""
        inspector = inspect(self.db.bind)
        table_names = inspector.get_table_names()

        # Exclut alembic_version (technique, pas métier)
        table_names = [t for t in table_names if t != "alembic_version"]

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for table_name in table_names:
                csv_content = self._table_to_csv(table_name)
                zf.writestr(f"{table_name}.csv", csv_content)

    def _table_to_csv(self, table_name: str) -> str:
        """Exporte une table en CSV (retourne le contenu en str)."""
        output = io.StringIO()
        # Utilisation de text() pour compatibilité SQLAlchemy 2.0
        result = self.db.execute(
            text(f'SELECT * FROM "{table_name}"')  # noqa: S608
        )
        rows = result.fetchall()
        columns = result.keys()

        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)

        return output.getvalue()
