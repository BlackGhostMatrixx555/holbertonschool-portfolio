"""
Modèle User — les comptes de la plateforme (super admin + organisateurs).
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid
# datetime : type Python pour les dates (utilisé pour les annotations)
from datetime import datetime

# Column : déclare une colonne ; String, Boolean, DateTime : types de colonnes SQL
from sqlalchemy import Column, String, Boolean, DateTime
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles (ex. un user a plusieurs camps)
from sqlalchemy.orm import relationship
# func : accès aux fonctions SQL côté base (ex. func.now() pour l'heure actuelle)
from sqlalchemy.sql import func

# Base : classe mère de tous les modèles ; pg_enum : crée un type ENUM PostgreSQL
from app.database import Base, pg_enum
# Énumérations des rôles et des statuts du compte
from app.models.enums import UserRole, UserStatus


# Déclaration de la classe User, qui correspond à une table SQL
class User(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "users"

    # Identifiant unique : clé primaire au format UUID, généré automatiquement par Python
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Prénom, limité à 100 caractères, obligatoire
    first_name = Column(String(100), nullable=False)
    # Nom de famille, limité à 100 caractères, obligatoire
    last_name = Column(String(100), nullable=False)
    # Email, unique (deux comptes ne peuvent pas partager le même) et indexé pour des recherches rapides
    email = Column(String(255), nullable=False, unique=True, index=True)
    # Numéro de téléphone, facultatif, utilisé pour la vérification par SMS
    phone_number = Column(String(20), nullable=True)  # <-- Nouveau champ
    # Hash bcrypt du mot de passe : on ne stocke jamais le mot de passe en clair
    password_hash = Column(String(255), nullable=False)
    # Rôle de l'utilisateur (super admin, directeur, SEM...), stocké comme ENUM PostgreSQL
    role = Column(pg_enum(UserRole, "user_role"), nullable=False)
    # Statut du compte (invité, actif, désactivé...), avec INVITED par défaut
    status = Column(
        pg_enum(UserStatus, "user_status"),
        nullable=False,
        default=UserStatus.INVITED,
    )
    # Date de création, remplie par la base elle-même au moment de l'insertion
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Champs pour la double authentification (2FA TOTP)
    # Secret TOTP de 32 caractères, partagé avec l'application d'authentification (Google Authenticator...)
    totp_secret = Column(String(32), nullable=True)
    # Indique si la 2FA est activée pour ce compte, désactivée par défaut
    is_2fa_enabled = Column(Boolean, nullable=False, default=False)

    # Relations
    # Liste des camps dont cet utilisateur est l'organisateur (lien inverse défini dans Camp)
    camps = relationship("Camp", back_populates="organizer")
    # Liste des backups déclenchés par cet utilisateur (lien inverse défini dans Backup)
    backups = relationship("Backup", back_populates="triggered_by_user")

    # Représentation textuelle de l'objet, utile pour le débogage et les logs
    def __repr__(self) -> str:
        # Affiche l'email et la valeur du rôle, par exemple <User admin@x.fr (super_admin)>
        return f"<User {self.email} ({self.role.value})>"
