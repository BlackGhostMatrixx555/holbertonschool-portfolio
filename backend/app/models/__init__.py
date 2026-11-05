"""
Point d'entrée des modèles.

Importer les modèles ici les enregistre tous dans Base.metadata : Alembic
(autogénération des migrations) et les tests voient ainsi toutes les tables.
Le reste du code importe depuis `app.models` plutôt que fichier par fichier.
"""
from app.models.user import User, UserRole, UserStatus
from app.models.camp import Camp, CampStatus
from app.models.registration import Registration
from app.models.camp_modality import CampModality, ModalityType
from app.models.landing_page import LandingPage, SeasonTheme
from app.models.contact_message import ContactChannel, ContactMessage, MessageStatus
from app.models.backup import Backup, BackupFormat
