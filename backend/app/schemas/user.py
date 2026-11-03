"""
Schémas Pydantic pour les utilisateurs.
"""
# uuid : pour typer les identifiants uniques des utilisateurs
import uuid
# datetime : pour typer les dates (ex. date de création du compte)
from datetime import datetime

# BaseModel : classe de base des schémas Pydantic
# ConfigDict : permet de configurer le comportement d'un schéma
# Field : permet d'ajouter des contraintes de validation sur un champ (longueur min/max, etc.)
from pydantic import BaseModel, ConfigDict, Field

# On importe notre type d'email personnalisé (DevEmailStr) en le renommant EmailStr
# Ainsi, dans le reste du fichier, on écrit EmailStr comme avec Pydantic classique
from app.schemas.types import DevEmailStr as EmailStr

# On importe les énumérations : les rôles possibles (super admin, organisateur...) et les statuts de compte
from app.models.enums import UserRole, UserStatus


# Schéma des données ENTRANTES : ce que le client envoie pour créer un utilisateur
class UserCreate(BaseModel):
    """Données pour créer un utilisateur (super admin uniquement)."""
    # Prénom : obligatoire (...), entre 1 et 100 caractères
    first_name: str = Field(..., min_length=1, max_length=100)
    # Nom de famille : obligatoire, entre 1 et 100 caractères
    last_name: str = Field(..., min_length=1, max_length=100)
    # Email : obligatoire, Pydantic vérifie qu'il a un format d'email valide
    email: EmailStr
    # Mot de passe en clair : obligatoire, entre 8 et 128 caractères (il sera haché avant d'être stocké)
    password: str = Field(..., min_length=8, max_length=128)
    # Rôle attribué à l'utilisateur : doit être une valeur de l'énumération UserRole
    role: UserRole


# Schéma des données SORTANTES : ce que l'API renvoie au client
class UserRead(BaseModel):
    """Utilisateur tel que renvoyé par l'API."""
    # from_attributes=True : permet de construire ce schéma directement depuis un objet SQLAlchemy (modèle User)
    model_config = ConfigDict(from_attributes=True)

    # Identifiant unique de l'utilisateur (UUID)
    id: uuid.UUID
    # Prénom de l'utilisateur
    first_name: str
    # Nom de famille de l'utilisateur
    last_name: str
    # Adresse email de l'utilisateur
    email: EmailStr
    # Numéro de téléphone : optionnel (peut être None), None par défaut
    phone_number: str | None = None  # <-- Nouveau champ
    # Rôle de l'utilisateur (super admin, organisateur...)
    role: UserRole
    # Statut du compte (actif, désactivé...)
    status: UserStatus
    # Date et heure de création du compte
    created_at: datetime
