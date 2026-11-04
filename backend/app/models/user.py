"""
Modèle User : les comptes de la plateforme (super admin et organisateurs).  # Docstring : décrit le rôle du modèle.

Fusion collins + tete-work : ajout du téléphone (vérification SMS) et des  # Historique : fusion de deux branches du projet.
champs de double authentification TOTP.  # Ajout de la vérification SMS et de la 2FA.
"""
import enum  # Module standard pour créer des énumérations (UserRole, UserStatus).
import uuid  # Module standard pour générer des identifiants uniques (UUID).

from sqlalchemy import Boolean, Column, DateTime, Enum, String, func  # Types de colonnes SQLAlchemy et fonction SQL func (ex. now()).
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre tables.

from app.db.base_class import Base  # Classe de base déclarative dont héritent tous les modèles.

class UserRole(str, enum.Enum):  # Énumération des rôles ; hériter de str permet la sérialisation JSON directe.
    SUPER_ADMIN = "super_admin"  # Super administrateur de la plateforme.
    ADMIN = "admin"  # Administrateur.
    SEM = "sem"  # Rôle métier défini par le projet (SEM).
    SWE = "swe"  # Rôle métier défini par le projet (SWE).
    SSM = "ssm"  # Rôle métier défini par le projet (SSM).
    DC = "dc"   # directeur de campus  # Responsable d'un campus.
    DT = "dt"   # directeur technique (cahier des charges, section 2)  # Responsable technique, cf. cahier des charges.
    ORGANIZER = "organizer"  # Organisateur de camps, rôle par défaut.

class UserStatus(str, enum.Enum):  # Énumération des statuts du compte ; même principe d'héritage de str.
    ACTIVE = "active"  # Compte actif, peut se connecter.
    INACTIVE = "inactive"   # ex. inscription en attente de validation  # Compte en attente, par exemple d'validation par un super admin.
    DISABLED = "disabled"  # Compte désactivé, connexion refusée.

class User(Base):  # Modèle représentant un compte utilisateur, hérite de Base.
    __tablename__ = "users"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement à la création.
    email = Column(String, unique=True, index=True, nullable=False)  # Adresse email unique, indexée pour les recherches de connexion, obligatoire.
    password_hash = Column(String, nullable=False)  # Hash du mot de passe, jamais le mot de passe en clair, obligatoire.
    first_name = Column(String, nullable=True)  # Prénom, facultatif.
    last_name = Column(String, nullable=True)  # Nom de famille, facultatif.
    phone_number = Column(String(20), nullable=True)  # Numéro de téléphone limité à 20 caractères, facultatif, utilisé pour la vérification SMS.
    role = Column(Enum(UserRole), default=UserRole.ORGANIZER, nullable=False)  # Rôle de l'utilisateur, ORGANIZER par défaut, obligatoire.
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)  # Statut du compte, ACTIVE par défaut, obligatoire.
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Date de création, remplie par la base avec l'heure courante, avec fuseau horaire.

    # Double authentification (TOTP, compatible Google Authenticator, etc.).  # Commentaire de section : 2FA par codes TOTP.
    # Le secret n'est jamais renvoyé par l'API après l'activation.  # Rappel de sécurité : le secret ne doit pas fuiter via l'API.
    totp_secret = Column(String(32), nullable=True)  # Secret TOTP de 32 caractères, vide tant que la 2FA n'est pas configurée.
    is_2fa_enabled = Column(Boolean, nullable=False, default=False, server_default="false")  # Indique si la 2FA est active, faux par défaut, au niveau Python comme en base.

    camps = relationship("Camp", back_populates="organizer", cascade="all, delete-orphan")  # Liste des camps organisés ; leur suppression entraîne celle de l'utilisateur.
    backups = relationship("Backup", back_populates="triggered_by_user")  # Liste des sauvegardes déclenchées par cet utilisateur, sans suppression en cascade.

    def __repr__(self):  # Représentation textuelle de l'objet, utile pour le débogage et les logs.
        return f"<User {self.email}>"  # Affiche l'email de l'utilisateur.