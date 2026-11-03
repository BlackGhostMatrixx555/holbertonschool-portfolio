"""
Routes pour les backups de base de données.

Réservé au super admin.
"""
# uuid : pour typer l'identifiant d'un backup
import uuid
# Path : manipulation des chemins de fichiers (utilisé indirectement via le service)
from pathlib import Path

# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, status
# FileResponse : renvoie un fichier téléchargeable au client
from fastapi.responses import FileResponse
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données par requête
from app.database import get_db
# require_role : fabrique de dépendance qui vérifie le rôle de l'utilisateur connecté
from app.dependencies import require_role
# User et UserRole : utilisateur connecté et énumération des rôles
from app.models import User, UserRole
# Schémas de validation : demande de backup et backup renvoyé
from app.schemas.backup import BackupCreate, BackupRead
# BackupService : logique de création, listage et récupération des fichiers de backup
from app.services.backup_service import BackupService

# Groupe de routes préfixé par /backups, rangé sous le tag "backups" dans la doc Swagger
router = APIRouter(prefix="/backups", tags=["backups"])


# Fabrique du service : FastAPI lui passe automatiquement la session de base de données
def get_backup_service(db: Session = Depends(get_db)) -> BackupService:
    # On renvoie un service branché sur cette session
    return BackupService(db)


# Dépendance réutilisable : n'accepte que les utilisateurs ayant le rôle SUPER_ADMIN
super_admin_only = require_role(UserRole.SUPER_ADMIN)


# Route POST /backups : génère un backup SQL ou CSV (201 à la création)
@router.post("", response_model=BackupRead, status_code=status.HTTP_201_CREATED)
def create_backup(
    # Corps de la requête : le format souhaité (SQL ou CSV)
    data: BackupCreate,
    # Service de backup injecté automatiquement
    service: BackupService = Depends(get_backup_service),
    # Utilisateur connecté, vérifié comme super admin par la dépendance
    current_user: User = Depends(super_admin_only),
):
    """Génère un backup SQL ou CSV. Réservé au super admin."""
    try:
        # Le service génère le fichier et enregistre le backup, en mémorisant qui l'a déclenché
        backup = service.create(data.format, triggered_by=current_user)
    except RuntimeError as e:
        # Erreur technique (par exemple l'outil de dump a échoué) : renvoyée en 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    # Backup créé, renvoyé au client
    return backup


# Route GET /backups : liste tous les backups existants
@router.get("", response_model=list[BackupRead])
def list_backups(
    service: BackupService = Depends(get_backup_service),
    # Le "_" indique que l'utilisateur est vérifié mais pas utilisé dans la fonction
    _: User = Depends(super_admin_only),
):
    """Liste tous les backups. Réservé au super admin."""
    return service.list()


# Route GET /backups/{backup_id}/download : télécharge le fichier d'un backup
@router.get("/{backup_id}/download")
def download_backup(
    # Identifiant du backup à télécharger, extrait de l'URL
    backup_id: uuid.UUID,
    service: BackupService = Depends(get_backup_service),
    _: User = Depends(super_admin_only),
):
    """Télécharge un backup. Réservé au super admin."""
    # On cherche l'entrée de backup en base
    backup = service.get_by_id(backup_id)
    # Si elle n'existe pas, erreur 404
    if backup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup introuvable.",
        )

    # On récupère le chemin réel du fichier sur le serveur
    file_path = service.get_file_path(backup)
    # L'entrée existe en base mais le fichier a disparu du disque : erreur 410 (Gone)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Le fichier de backup a été supprimé du serveur.",
        )

    # On renvoie le fichier en téléchargement, sans savoir à l'avance son type exact
    return FileResponse(
        # Chemin du fichier à envoyer
        path=file_path,
        # Nom proposé au téléchargement dans le navigateur
        filename=file_path.name,
        # Type générique : le navigateur télécharge le fichier au lieu de tenter de l'afficher
        media_type="application/octet-stream",
    )
