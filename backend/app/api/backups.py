"""Routes des sauvegardes (super admin uniquement) : créer, lister, télécharger."""  # Docstring du module : toutes les routes sont réservées au super admin.
from uuid import UUID  # Type pour l'identifiant de sauvegarde passé dans l'URL.

from fastapi import APIRouter, Depends, status  # APIRouter pour grouper les routes, Depends pour l'injection, status pour les codes HTTP nommés.
from fastapi.responses import FileResponse  # Réponse HTTP qui renvoie un fichier au client.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import require_super_admin  # Dépendance qui vérifie le jeton et exige le rôle super admin, sinon refuse l'accès.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.backup import BackupCreate, BackupView  # Schéma d'entrée (format demandé) et schéma de sortie (description d'une sauvegarde).
from app.services import backup_service  # Couche service contenant la logique de création, listing et téléchargement des sauvegardes.

router = APIRouter(prefix="/backups", tags=["Sauvegardes"])  # Routeur préfixé par /backups, regroupé sous "Sauvegardes" dans Swagger.

@router.post("", response_model=BackupView, status_code=status.HTTP_201_CREATED)  # Route POST sur /backups : création d'une sauvegarde, réponse 201.
def create_backup(payload: BackupCreate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Reçoit le format demandé, exige un super admin et injecte la session.
    return backup_service.create(db, payload.format, current_user)  # Délègue la création au service, en lui transmettant le format et l'auteur de la sauvegarde.

@router.get("", response_model=list[BackupView])  # Route GET sur /backups : liste des sauvegardes existantes.
def list_backups(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Exige un super admin ; l'utilisateur n'est pas utilisé dans le corps, d'où le nom "_".
    return backup_service.list_backups(db)  # Délègue au service, qui renvoie la liste des sauvegardes.

@router.get("/{backup_id}/download")  # Route GET sur /backups/{id}/download : téléchargement du fichier d'une sauvegarde. Pas de response_model car le retour est un fichier.
def download_backup(backup_id: UUID, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Identifiant de la sauvegarde, vérification super admin et session.
    path = backup_service.get_file(db, backup_id)  # Demande au service le chemin du fichier correspondant à cette sauvegarde.
    media_type = "application/sql" if path.suffix == ".sql" else "application/zip"  # Déduit le type MIME selon l'extension : .sql pour un export SQL, sinon archive zip.
    return FileResponse(path, media_type=media_type, filename=path.name)  # Renvoie le fichier au client avec le bon type MIME et le nom de fichier d'origine, pour qu'il soit téléchargé.