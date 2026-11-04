"""Routes du chatbot : public (visiteur) et organisateur (historique, statistiques)."""  # Docstring du module : une route publique pour le visiteur, deux routes réservées à l'organisateur.
from uuid import UUID  # Type pour les identifiants de camp passés dans l'URL.

from fastapi import APIRouter, Depends, Query  # APIRouter pour grouper les routes, Depends pour l'injection, Query pour les paramètres de l'URL.
from pymongo.database import Database  # Type d'une base MongoDB (l'historique des conversations y est stocké).
from sqlalchemy.orm import Session  # Type d'une session de base de données relationnelle (PostgreSQL ou équivalent).

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.mongo import get_mongo_db  # Fournit une connexion à la base MongoDB.
from app.db.session import get_db  # Fournit une session de base de données relationnelle.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.chat import ChatReply, ChatRequest, ChatStats, ConversationView  # Schémas : question du visiteur, réponse, statistiques et historique.
from app.services import chat_service  # Couche service contenant la logique du chatbot.

router = APIRouter(tags=["Chatbot"])  # Routeur sans préfixe, regroupé sous "Chatbot" dans la documentation Swagger.

@router.post("/camps/{slug}/chat", response_model=ChatReply)  # Route POST publique : le visiteur envoie une question pour le camp identifié par son slug. Aucune authentification.
def chat(slug: str, payload: ChatRequest, db: Session = Depends(get_db), mongo: Database = Depends(get_mongo_db)):  # Reçoit le slug, la question et les deux connexions (relationnelle et MongoDB).
    """Le visiteur pose une question ; la réponse et la question sont historisées dans MongoDB."""  # Docstring de la route, visible dans la documentation Swagger.
    return chat_service.handle_message(db, mongo, slug, payload)  # Délègue au service, qui génère la réponse et enregistre l'échange dans MongoDB.

@router.get("/camps/{camp_id}/chat/conversations", response_model=list[ConversationView])  # Route GET réservée à l'organisateur : historique des conversations d'un camp.
def list_conversations(  # Renvoie la liste des conversations.
    camp_id: UUID,  # Identifiant du camp, validé comme UUID.
    limit: int = Query(default=50, ge=1, le=200),  # Nombre maximal de conversations à renvoyer : 50 par défaut, entre 1 et 200 ; une valeur hors bornes est refusée.
    current_user: User = Depends(get_current_user),  # Utilisateur connecté (obligatoire).
    db: Session = Depends(get_db),  # Session relationnelle, pour vérifier les droits et les données du camp.
    mongo: Database = Depends(get_mongo_db),  # Connexion MongoDB, où sont stockées les conversations.
):
    return chat_service.list_conversations(db, mongo, camp_id, current_user, limit)  # Délègue au service, qui vérifie que l'utilisateur gère ce camp avant de renvoyer l'historique limité.

@router.get("/camps/{camp_id}/chat/stats", response_model=ChatStats)  # Route GET réservée à l'organisateur : statistiques d'utilisation du chatbot pour un camp.
def chat_stats(  # Renvoie les statistiques.
    camp_id: UUID,  # Identifiant du camp, validé comme UUID.
    current_user: User = Depends(get_current_user),  # Utilisateur connecté (obligatoire).
    db: Session = Depends(get_db),  # Session relationnelle.
    mongo: Database = Depends(get_mongo_db),  # Connexion MongoDB, source des données calculées.
):
    return chat_service.stats(db, mongo, camp_id, current_user)  # Délègue au service, qui vérifie les droits de l'utilisateur puis calcule les statistiques.