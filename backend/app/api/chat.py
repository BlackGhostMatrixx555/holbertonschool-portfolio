"""Routes du chatbot : public (visiteur) et organisateur (historique, statistiques)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.mongo import get_mongo_db
from app.db.session import get_db
from app.models import User
from app.schemas.chat import ChatReply, ChatRequest, ChatStats, ConversationView
from app.services import chat_service

router = APIRouter(tags=["Chatbot"])


@router.post("/camps/{slug}/chat", response_model=ChatReply)
def chat(slug: str, payload: ChatRequest, db: Session = Depends(get_db), mongo: Database = Depends(get_mongo_db)):
    """Le visiteur pose une question ; la réponse et la question sont historisées dans MongoDB."""
    return chat_service.handle_message(db, mongo, slug, payload)


@router.get("/camps/{camp_id}/chat/conversations", response_model=list[ConversationView])
def list_conversations(
    camp_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mongo: Database = Depends(get_mongo_db),
):
    return chat_service.list_conversations(db, mongo, camp_id, current_user, limit)


@router.get("/camps/{camp_id}/chat/stats", response_model=ChatStats)
def chat_stats(
    camp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mongo: Database = Depends(get_mongo_db),
):
    return chat_service.stats(db, mongo, camp_id, current_user)
