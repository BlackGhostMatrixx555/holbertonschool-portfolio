"""
Schémas Pydantic pour le chatbot et la hotline.
"""
# uuid : module pour manipuler les identifiants uniques (UUID)
import uuid
# BaseModel : classe de base des schémas Pydantic
# Field : permet d'ajouter des contraintes de validation sur un champ (longueur min/max, etc.)
from pydantic import BaseModel, Field
# ContactChannel : énumération des canaux de contact possibles (chatbot, hotline, etc.)
from app.models.enums import ContactChannel

# Schéma des données ENTRANTES : ce que le visiteur envoie au chatbot
class ChatRequest(BaseModel):
    """Message envoyé par un visiteur au chatbot."""
    # Question du visiteur : obligatoire (...), entre 1 et 1000 caractères (évite les messages vides ou démesurés)
    message: str = Field(..., min_length=1, max_length=1000)
    # Camp concerné par la question : optionnel (None si la question est générale), pour que le chatbot adapte sa réponse
    camp_id: uuid.UUID | None = None

# Schéma des données SORTANTES : ce que le chatbot renvoie au visiteur
class ChatResponse(BaseModel):
    """Réponse renvoyée par le chatbot."""
    # Texte de la réponse affiché au visiteur
    reply: str
    # Canal d'origine de la réponse : vaut "chatbot" par défaut (permet de distinguer chatbot et hotline dans l'historique)
    channel: ContactChannel = ContactChannel.CHATBOT

# Schéma des données ENTRANTES : ce que le visiteur envoie via le formulaire de contact (hotline)
class ContactMessageCreate(BaseModel):
    """Message envoyé via le formulaire de contact (hotline)."""
    # Nom de l'expéditeur : obligatoire, entre 1 et 150 caractères
    name: str = Field(..., min_length=1, max_length=150)
    # Email de l'expéditeur pour pouvoir lui répondre : obligatoire, 255 caractères maximum (simple texte, pas validé comme un vrai email)
    email: str = Field(..., max_length=255)
    # Contenu du message : obligatoire, au moins 1 caractère (aucune limite maximale)
    message: str = Field(..., min_length=1)
    # Camp concerné par la demande : optionnel (None si la demande est générale)
    camp_id: uuid.UUID | None = None
