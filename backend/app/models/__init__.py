"""
Regroupe tous les modèles.

Importer ce package suffit à charger l'ensemble des modèles : c'est
nécessaire pour que SQLAlchemy puisse résoudre les relations entre eux
(ex. relationship("Camp") dans user.py), et pour qu'Alembic détecte
toutes les tables lors de la génération des migrations.
"""
from app.models.enums import (
    UserRole, UserStatus, CampStatus, ModalityType,
    SeasonTheme, ContactChannel, BackupFormat,
)
from app.models.user import User
from app.models.camp import Camp, CampModality
from app.models.landing_page import LandingPage
from app.models.registration import Registration
from app.models.contact_backup import ContactMessage, Backup

__all__ = [
    "UserRole", "UserStatus", "CampStatus", "ModalityType",
    "SeasonTheme", "ContactChannel", "BackupFormat",
    "User", "Camp", "CampModality", "LandingPage",
    "Registration", "ContactMessage", "Backup",
]
