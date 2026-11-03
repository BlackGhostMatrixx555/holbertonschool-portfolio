"""
Schémas Pydantic pour les backups.
"""
# uuid : module pour manipuler les identifiants uniques (UUID)
import uuid
# datetime : type pour une date avec heure
from datetime import datetime

# BaseModel : classe de base des schémas Pydantic
# ConfigDict : permet de configurer le comportement d'un schéma
from pydantic import BaseModel, ConfigDict

# BackupFormat : énumération des formats de sauvegarde possibles (SQL, CSV)
from app.models.enums import BackupFormat


# Schéma ENTRANT : ce que le client envoie pour déclencher un backup
class BackupCreate(BaseModel):
    """Données envoyées pour déclencher un backup."""

    # Format souhaité pour l'export : seules les valeurs de l'énumération BackupFormat sont acceptées
    format: BackupFormat


# Schéma SORTANT : ce que l'API renvoie pour décrire un backup
class BackupRead(BaseModel):
    """Backup tel que renvoyé par l'API."""

    # from_attributes=True : permet de construire ce schéma directement depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    # Identifiant unique du backup, généré par le serveur
    id: uuid.UUID
    # Format du backup (SQL ou CSV)
    format: BackupFormat
    # Identifiant du super admin qui a déclenché le backup (traçabilité)
    triggered_by: uuid.UUID
    # Chemin du fichier de sauvegarde généré sur le serveur
    file_path: str
    # Taille du fichier en kilo-octets : None si elle n'a pas été calculée
    file_size_kb: int | None
    # Date et heure de création du backup, renseignées par le serveur
    created_at: datetime
