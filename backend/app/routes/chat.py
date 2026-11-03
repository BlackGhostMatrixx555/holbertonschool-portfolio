"""
Routes pour le chatbot et la hotline.
Ces routes sont publiques (pas de JWT requis).
"""
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données par requête
from app.database import get_db
# Schémas : requête et réponse du chatbot, message de la hotline
from app.schemas.chat import ChatRequest, ChatResponse, ContactMessageCreate
# ChatService : contient la logique du chatbot et l'enregistrement des messages de contact
from app.services.chat_service import ChatService

# Groupe de routes préfixé par /contact, rangé sous le tag "contact" dans la doc Swagger
router = APIRouter(prefix="/contact", tags=["contact"])


# Fabrique du service : FastAPI lui passe automatiquement la session de base de données
def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    # On renvoie un service branché sur cette session
    return ChatService(db)


# Route POST /contact/chat : envoie un message au chatbot et renvoie sa réponse (200 OK)
@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(
    # Corps de la requête, validé automatiquement : le message et l'éventuel identifiant du camp
    data: ChatRequest,
    # Service du chatbot injecté automatiquement
    service: ChatService = Depends(get_chat_service),
):
    """Envoie un message au chatbot et récupère sa réponse."""
    # Le service calcule la réponse du bot à partir du message
    reply = service.process_message(data)
    # On renvoie la réponse en précisant le canal, ici le chatbot
    return ChatResponse(reply=reply, channel="chatbot")


# Route POST /contact/hotline : enregistre un message du formulaire de contact (201 à la création)
@router.post("/hotline", status_code=status.HTTP_201_CREATED)
def send_hotline_message(
    # Corps de la requête, validé automatiquement : nom, email, message et éventuel camp concerné
    data: ContactMessageCreate,
    # Service du chatbot/hotline injecté automatiquement
    service: ChatService = Depends(get_chat_service),
):
    """Enregistre un message envoyé via la hotline (formulaire de contact)."""
    # Le service enregistre le message en base pour qu'un organisateur puisse le traiter
    service.create_contact_message(data)
    # On confirme au visiteur que son message est bien parti
    return {"status": "ok", "message": "Votre message a bien été envoyé."}
