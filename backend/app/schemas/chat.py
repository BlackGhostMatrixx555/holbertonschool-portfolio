"""Schémas du chatbot de la landing page."""  # Docstring du module : schémas du chatbot de la landing page.
from datetime import datetime  # Type des dates et heures, utilisé pour les horodatages des messages et conversations.
from typing import Literal  # Permet de restreindre une valeur à un ensemble fixe de chaînes.

from pydantic import BaseModel, Field  # Classe de base Pydantic et fonction de définition de contraintes de champs.

class ChatRequest(BaseModel):  # Requête envoyée par le visiteur au chatbot.
    # Identifiant de session généré par le navigateur (UUID) ; absent au 1er message.  # Explication du rôle de session_id.
    session_id: str | None = Field(default=None, min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")  # Identifiant optionnel, 8 à 64 caractères alphanumériques ou tirets.
    message: str = Field(min_length=1, max_length=500)  # Message du visiteur, entre 1 et 500 caractères.

class ChatReply(BaseModel):  # Réponse renvoyée par le chatbot.
    session_id: str  # Identifiant de la session, à réutiliser pour les messages suivants.
    reply: str  # Texte de la réponse du bot.
    intent: str  # Intention reconnue dans le message du visiteur.

class ChatMessage(BaseModel):  # Un message d'une conversation.
    role: Literal["visitor", "bot"]  # Auteur du message : le visiteur ou le bot.
    content: str  # Contenu textuel du message.
    intent: str | None = None  # Intention associée, facultative (surtout pour les réponses du bot).
    at: datetime  # Date et heure d'envoi du message.

class ConversationView(BaseModel):  # Conversation complète renvoyée par l'API.
    session_id: str  # Identifiant de la session de conversation.
    camp_slug: str  # Identifiant lisible du camp concerné dans l'URL.
    created_at: datetime  # Date de création de la conversation.
    updated_at: datetime  # Date de la dernière mise à jour de la conversation.
    messages: list[ChatMessage]  # Liste ordonnée des messages échangés.

class IntentCount(BaseModel):  # Nombre d'occurrences d'une intention donnée.
    intent: str  # Nom de l'intention.
    count: int  # Nombre de fois où elle a été reconnue.

class ChatStats(BaseModel):  # Statistiques globales du chatbot.
    conversations: int  # Nombre total de conversations.
    visitor_messages: int  # Nombre total de messages envoyés par les visiteurs.
    top_intents: list[IntentCount]  # Intentions les plus fréquentes.