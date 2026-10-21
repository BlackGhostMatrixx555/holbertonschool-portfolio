"""
Routes pour le chatbot et la hotline.
Ces routes sont publiques (pas de JWT requis).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ContactMessageCreate
from app.services.chat_service import ChatService

router = APIRouter(prefix="/contact", tags=["contact"])


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(
    data: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Envoie un message au chatbot et récupère sa réponse."""
    reply = service.process_message(data)
    return ChatResponse(reply=reply, channel="chatbot")


@router.post("/hotline", status_code=status.HTTP_201_CREATED)
def send_hotline_message(
    data: ContactMessageCreate,
    service: ChatService = Depends(get_chat_service),
):
    """Enregistre un message envoyé via la hotline (formulaire de contact)."""
    service.create_contact_message(data)
    return {"status": "ok", "message": "Votre message a bien été envoyé."}
