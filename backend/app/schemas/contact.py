"""Schémas des messages de contact (hotline)."""  # Docstring du module : schémas des messages de contact.
from datetime import datetime  # Type des dates et heures, utilisé pour la date de création du message.
from uuid import UUID  # Type des identifiants (message, camp).

from pydantic import BaseModel, ConfigDict, EmailStr, Field  # Classes de base Pydantic, configuration, validation d'email et contraintes de champs.

from app.models import ContactChannel, MessageStatus  # Énumérations du canal de contact et du statut du message.

class ContactMessageCreate(BaseModel):  # Données envoyées via le formulaire de contact.
    name: str = Field(min_length=1, max_length=100)  # Nom de l'expéditeur, entre 1 et 100 caractères.
    email: EmailStr  # Adresse email de l'expéditeur, validée au format email.
    # Longueur maximale : limite le spam et les requêtes trop lourdes.  # Explication de la limite de longueur du message.
    message: str = Field(min_length=1, max_length=2000)  # Contenu du message, entre 1 et 2000 caractères.
    channel: ContactChannel = ContactChannel.HOTLINE  # Canal d'origine du message, par défaut la hotline.

class ContactMessageStatusUpdate(BaseModel):  # Données pour changer le statut d'un message.
    status: MessageStatus  # Nouveau statut du message.

class ContactMessageView(BaseModel):  # Représentation d'un message de contact renvoyée par l'API.
    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant du message.
    camp_id: UUID  # Identifiant du camp concerné.
    name: str  # Nom de l'expéditeur.
    email: EmailStr  # Adresse email de l'expéditeur.
    message: str  # Contenu du message.
    channel: ContactChannel  # Canal d'origine du message.
    status: MessageStatus  # Statut actuel du message.
    created_at: datetime | None = None  # Date de création du message, absente par défaut.