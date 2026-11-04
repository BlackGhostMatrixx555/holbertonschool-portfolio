"""Schémas de l'historique des sauvegardes."""  # Docstring du module : schémas de l'historique des sauvegardes.
from datetime import datetime  # Type des horodatages, utilisé pour la date de création de la sauvegarde.
from uuid import UUID  # Type des identifiants (sauvegarde, utilisateur déclencheur).

from pydantic import BaseModel, ConfigDict  # Classe de base Pydantic et configuration du modèle.

from app.models import BackupFormat  # Énumération des formats de sauvegarde disponibles.

class BackupCreate(BaseModel):  # Données envoyées pour déclencher une sauvegarde.
    format: BackupFormat  # Format de la sauvegarde à produire.

class BackupView(BaseModel):  # Sauvegarde telle que renvoyée par l'API.
    """Une sauvegarde de l'historique (le chemin sur le serveur n'est pas exposé)."""  # Docstring : le chemin de fichier est volontairement omis pour des raisons de sécurité.

    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant de la sauvegarde.
    format: BackupFormat  # Format de la sauvegarde.
    triggered_by: UUID  # Identifiant de l'utilisateur qui a déclenché la sauvegarde.
    file_size_kb: int | None  # Taille du fichier en kilo-octets, absente si inconnue.
    created_at: datetime | None  # Date de création de la sauvegarde, absente si inconnue.