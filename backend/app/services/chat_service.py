"""
Chatbot simple de la landing page, avec historique stocké dans MongoDB.

Le "bot" reconnaît l'intention du visiteur par mots-clés (dates, lieu,
âge...) et répond avec les vraies données du camp lues dans PostgreSQL.
Chaque échange est ajouté au document de la conversation dans MongoDB.
Le cahier des charges prévoit un chatbot simple ; un chatbot IA
conversationnel est explicitement hors périmètre du MVP.
"""
import unicodedata
import uuid
from datetime import datetime, timezone
from uuid import UUID

from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.db.mongo import CONVERSATIONS
from app.models import Camp, User
from app.schemas.chat import ChatRequest
from app.services import camp_service

# Intention -> mots-clés (sans accents, en minuscules). L'ordre compte :
# la première intention trouvée l'emporte.
INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "registration": ("inscri", "register", "sign up", "reserver", "reservation"),
    "places": ("place", "complet", "reste", "spots", "capacite"),
    "dates": ("date", "quand", "when", "debut", "fin", "commence", "duree"),
    "location": (" ou ", "lieu", "ville", "adresse", "where", "city"),
    "age": ("age", "ans", "old", "mineur", "majeur", "niveau", "eligib", "condition"),
    "program": ("programme", "contenu", "apprendre", "activite", "program", "learn"),
    "human": ("humain", "contact", "telephone", "email", "hotline", "parler", "human"),
    "greeting": ("bonjour", "salut", "hello", " hi ", "bonsoir", "coucou"),
}


def _normalize(text: str) -> str:
    """'Où est-il ?' -> ' ou est-il ? ' (sans accents, minuscules, entouré d'espaces).

    Les espaces autour permettent de chercher un mot entier : " ou " ne trouve
    pas "ou" à l'intérieur de "beaucoup".
    """
    without_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(char if char.isalnum() else " " for char in without_accents.lower())
    return f" {cleaned} "


def detect_intent(message: str) -> str:
    text = _normalize(message)
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return intent
    return "unknown"


def build_reply(intent: str, camp: Camp) -> str:
    """Construit la réponse à partir des données réelles du camp."""
    start, end = camp.start_date.strftime("%d/%m/%Y"), camp.end_date.strftime("%d/%m/%Y")
    replies = {
        "greeting": f"Bonjour ! Je suis l'assistant du camp « {camp.name} ». "
                    "Posez-moi une question sur les dates, le lieu, l'âge requis ou les inscriptions.",
        "dates": f"Le camp a lieu du {start} au {end}.",
        "location": f"Le camp se déroule à {camp.city}." if camp.city else
                    "Le lieu exact sera communiqué par l'organisateur.",
        "age": (f"Ce camp est ouvert à partir de {camp.age} ans." if camp.age else "Ce camp est ouvert à tous les âges.")
               + (" Conditions : " + " ; ".join(m.label for m in camp.modalities) + "." if camp.modalities else ""),
        "places": f"Il reste {camp.remaining_places} place(s)." if camp.remaining_places > 0 else
                  "Ce camp est complet, désolé.",
        "registration": "Pour vous inscrire, remplissez le formulaire de cette page : "
                        "prénom, nom, email, puis confirmez votre participation.",
        "program": camp.description or "Le programme détaillé sera bientôt publié.",
        "human": "Vous pouvez joindre l'équipe via le formulaire de contact (hotline) de cette page. "
                 "Un organisateur vous répondra par email.",
    }
    return replies.get(
        intent,
        "Je n'ai pas compris. Je peux vous renseigner sur les dates, le lieu, l'âge requis, "
        "les places restantes ou l'inscription.",
    )


def handle_message(db: Session, mongo: Database, slug: str, payload: ChatRequest) -> dict:
    camp = camp_service.get_public_camp(db, slug)  # 404 si le camp n'est pas publié
    session_id = payload.session_id or str(uuid.uuid4())
    intent = detect_intent(payload.message)
    reply = build_reply(intent, camp)
    now = datetime.now(timezone.utc)

    try:
        # Une seule opération atomique :
        # - upsert=True crée le document au premier message ;
        # - $setOnInsert ne remplit ces champs qu'à la création ;
        # - $push ajoute les deux messages à la fin du tableau "messages".
        mongo[CONVERSATIONS].update_one(
            {"session_id": session_id, "camp_id": str(camp.id)},
            {
                "$setOnInsert": {"camp_slug": camp.slug, "created_at": now},
                "$set": {"updated_at": now},
                "$push": {"messages": {"$each": [
                    {"role": "visitor", "content": payload.message, "intent": intent, "at": now},
                    {"role": "bot", "content": reply, "intent": intent, "at": now},
                ]}},
            },
            upsert=True,
        )
    except DuplicateKeyError as exc:
        # Ce session_id appartient déjà à la conversation d'un autre camp.
        raise ConflictError("Session de chat invalide pour ce camp.") from exc
    except PyMongoError as exc:
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc

    return {"session_id": session_id, "reply": reply, "intent": intent}


def list_conversations(db: Session, mongo: Database, camp_id: UUID, user: User, limit: int = 50) -> list[dict]:
    camp_service.get_managed_camp(db, camp_id, user)  # contrôle d'accès dans PostgreSQL
    try:
        cursor = (
            mongo[CONVERSATIONS]
            .find({"camp_id": str(camp_id)}, {"_id": 0})  # projection : on exclut _id
            .sort("updated_at", DESCENDING)
            .limit(limit)
        )
        return list(cursor)
    except PyMongoError as exc:
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc


def stats(db: Session, mongo: Database, camp_id: UUID, user: User) -> dict:
    """
    Statistiques des questions posées, calculées par MongoDB (pipeline d'agrégation) :
    $match (ce camp) -> $unwind (un document par message) -> $match (messages visiteurs)
    -> $group (compte par intention) -> $sort -> $limit.
    """
    camp_service.get_managed_camp(db, camp_id, user)
    collection = mongo[CONVERSATIONS]
    pipeline = [
        {"$match": {"camp_id": str(camp_id)}},
        {"$unwind": "$messages"},
        {"$match": {"messages.role": "visitor"}},
        {"$group": {"_id": "$messages.intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    try:
        groups = list(collection.aggregate(pipeline))
        conversations = collection.count_documents({"camp_id": str(camp_id)})
    except PyMongoError as exc:
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc

    return {
        "conversations": conversations,
        "visitor_messages": sum(group["count"] for group in groups),
        "top_intents": [{"intent": group["_id"], "count": group["count"]} for group in groups[:5]],
    }
