"""Schémas des comptes utilisateurs."""  # Docstring du module : schémas des comptes utilisateurs.
from uuid import UUID  # Type des identifiants d'utilisateur.

from pydantic import BaseModel, ConfigDict, EmailStr, Field  # Classes de base Pydantic, configuration, validation d'email et contraintes de champs.

from app.models import UserRole, UserStatus  # Énumérations des rôles et des statuts de compte.

PHONE_PATTERN = r"^\+?[0-9 .-]{6,20}$"  # Expression régulière du numéro de téléphone : + facultatif, chiffres, espaces, points ou tirets, entre 6 et 20 caractères.

class UserCreate(BaseModel):  # Données nécessaires à la création d'un compte.
    email: EmailStr  # Adresse email, validée au format email.
    # 12 caractères minimum : recommandation de l'ANSSI pour un mot de passe seul.  # Justification de la longueur minimale du mot de passe.
    password: str = Field(min_length=12, max_length=128)  # Mot de passe entre 12 et 128 caractères.
    first_name: str = Field(min_length=1, max_length=100)  # Prénom obligatoire, entre 1 et 100 caractères.
    last_name: str = Field(min_length=1, max_length=100)  # Nom obligatoire, entre 1 et 100 caractères.
    role: UserRole = UserRole.ORGANIZER  # Rôle du compte, organisateur par défaut.

class UserRoleUpdate(BaseModel):  # Données pour changer le rôle d'un compte.
    role: UserRole  # Nouveau rôle à attribuer.

class UserStatusUpdate(BaseModel):  # Données pour changer le statut d'un compte.
    status: UserStatus  # Nouveau statut à appliquer.

class ProfileUpdate(BaseModel):  # Données modifiables par l'utilisateur sur son propre profil.
    """Ce qu'un utilisateur peut modifier lui-même (ni son rôle, ni son statut)."""  # Docstring : seuls le nom, le prénom et le téléphone sont modifiables.

    first_name: str | None = Field(default=None, min_length=1, max_length=100)  # Nouveau prénom facultatif, entre 1 et 100 caractères si fourni.
    last_name: str | None = Field(default=None, min_length=1, max_length=100)  # Nouveau nom facultatif, entre 1 et 100 caractères si fourni.
    phone_number: str | None = Field(default=None, pattern=PHONE_PATTERN)  # Nouveau téléphone facultatif, au format défini par PHONE_PATTERN.

class UserView(BaseModel):  # Représentation publique d'un compte renvoyée par l'API.
    """Vue publique d'un compte : jamais de password_hash ni de totp_secret."""  # Docstring : les secrets ne sont jamais exposés.

    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant du compte.
    email: str  # Adresse email du compte.
    first_name: str | None  # Prénom, pouvant être vide.
    last_name: str | None  # Nom, pouvant être vide.
    phone_number: str | None = None  # Téléphone, absent par défaut.
    role: UserRole  # Rôle du compte.
    status: UserStatus  # Statut du compte.
    is_2fa_enabled: bool = False  # Indique si la double authentification est activée, désactivée par défaut.