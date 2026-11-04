"""Schémas des inscriptions aux camps."""  # Docstring du module : schémas des inscriptions aux camps.
from datetime import datetime  # Type des dates et heures, utilisé pour la date de création.
from uuid import UUID  # Type des identifiants (inscription, camp).

from pydantic import BaseModel, ConfigDict, EmailStr, Field  # Classes de base Pydantic, configuration, validation d'email et contraintes de champs.

class RegistrationCreate(BaseModel):  # Données envoyées par le formulaire public d'inscription.
    """Formulaire public d'inscription (cahier des charges, module 4.4)."""  # Docstring : formulaire public, référence au cahier des charges.

    first_name: str = Field(min_length=1, max_length=100)  # Prénom obligatoire, entre 1 et 100 caractères.
    last_name: str = Field(min_length=1, max_length=100)  # Nom obligatoire, entre 1 et 100 caractères.
    email: EmailStr  # Adresse email, validée au format email.
    comment: str | None = Field(default=None, max_length=1000)  # Commentaire facultatif, 1000 caractères maximum.

class AttendanceUpdate(BaseModel):  # Données pour modifier la présence d'un inscrit.
    confirmed: bool  # Présence confirmée ou non.

class RegistrationView(BaseModel):  # Représentation d'une inscription renvoyée par l'API.
    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant de l'inscription.
    camp_id: UUID  # Identifiant du camp concerné.
    first_name: str  # Prénom de l'inscrit.
    last_name: str  # Nom de l'inscrit.
    email: EmailStr  # Adresse email de l'inscrit.
    comment: str | None  # Commentaire laissé lors de l'inscription, pouvant être vide.
    confirmed: bool  # Indique si la présence est confirmée.
    created_at: datetime | None = None  # Date de création de l'inscription, absente par défaut.