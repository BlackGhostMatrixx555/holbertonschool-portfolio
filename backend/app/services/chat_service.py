"""
Chatbot simple de la landing page, avec historique stocké dans MongoDB.

Le "bot" reconnaît l'intention du visiteur par mots-clés (dates, lieu,
âge...) et répond avec les vraies données du camp lues dans PostgreSQL.
Chaque échange est ajouté au document de la conversation dans MongoDB.
Le cahier des charges prévoit un chatbot simple ; un chatbot IA
conversationnel est explicitement hors périmètre du MVP.
"""
import unicodedata  # Suppression des accents lors de la normalisation du texte.
import uuid  # Génération d'un identifiant de session quand le visiteur n'en a pas.
from datetime import datetime, timezone  # Horodatage des messages en UTC.
from uuid import UUID  # Type des identifiants de camp et d'utilisateur.

from pymongo import DESCENDING  # Constante de tri décroissant pour MongoDB.
from pymongo.database import Database  # Type de la base MongoDB.
from pymongo.errors import DuplicateKeyError, PyMongoError  # Erreurs d'écriture en double et erreurs MongoDB génériques.
from sqlalchemy.orm import Session  # Session SQLAlchemy pour PostgreSQL.

from app.core.exceptions import ConflictError, ServiceUnavailableError  # Erreurs métier (conflit, service indisponible).
from app.db.mongo import CONVERSATIONS  # Nom de la collection des conversations.
from app.models import Camp, User  # Modèles camp et utilisateur.
from app.schemas.chat import ChatRequest  # Schéma du message envoyé par le visiteur.
from app.services import camp_service  # Accès aux camps (lecture publique et contrôle de gestion).

# Intention -> mots-clés (sans accents, en minuscules). L'ordre compte :
# la première intention trouvée l'emporte.
INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {  # Dictionnaire des intentions reconnues et de leurs mots-clés.
    "registration": ("inscri", "register", "sign up", "reserver", "reservation"),  # Questions sur l'inscription.
    "places": ("place", "complet", "reste", "spots", "capacite"),  # Questions sur les places disponibles.
    "dates": ("date", "quand", "when", "debut", "fin", "commence", "duree"),  # Questions sur le calendrier.
    "location": (" ou ", "lieu", "ville", "adresse", "where", "city"),  # Questions sur le lieu (" ou " avec espaces pour éviter les faux positifs).
    "age": ("age", "ans", "old", "mineur", "majeur", "niveau", "eligib", "condition"),  # Questions sur l'âge et les conditions.
    "program": ("programme", "contenu", "apprendre", "activite", "program", "learn"),  # Questions sur le contenu du camp.
    "human": ("humain", "contact", "telephone", "email", "hotline", "parler", "human"),  # Demande de parler à un humain.
    "greeting": ("bonjour", "salut", "hello", " hi ", "bonsoir", "coucou"),  # Salutations.
}

def _normalize(text: str) -> str:  # Prépare le texte pour la recherche de mots-clés.
    """'Où est-il ?' -> ' ou est-il ? ' (sans accents, minuscules, entouré d'espaces).

    Les espaces autour permettent de chercher un mot entier : " ou " ne trouve
    pas "ou" à l'intérieur de "beaucoup".
    """
    without_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")  # Décompose les caractères accentués puis supprime les accents.
    cleaned = "".join(char if char.isalnum() else " " for char in without_accents.lower())  # Met en minuscules et remplace la ponctuation par des espaces.
    return f" {cleaned} "  # Ajoute un espace de chaque côté pour permettre la recherche de mots entiers.

def detect_intent(message: str) -> str:  # Détermine l'intention d'un message.
    text = _normalize(message)  # Normalise le message avant la recherche.
    for intent, keywords in INTENT_KEYWORDS.items():  # Parcourt les intentions dans l'ordre de définition.
        if any(keyword in text for keyword in keywords):  # Vrai dès qu'un mot-clé de l'intention est présent.
            return intent  # La première intention trouvée l'emporte.
    return "unknown"  # Aucune intention reconnue.

def build_reply(intent: str, camp: Camp) -> str:  # Construit la réponse textuelle selon l'intention.
    """Construit la réponse à partir des données réelles du camp."""
    start, end = camp.start_date.strftime("%d/%m/%Y"), camp.end_date.strftime("%d/%m/%Y")  # Dates formatées en jour/mois/année.
    replies = {  # Réponse pour chaque intention, calculée à partir des données du camp.
        "greeting": f"Bonjour ! Je suis l'assistant du camp « {camp.name} ». "  # Salutation avec le nom du camp.
                    "Posez-moi une question sur les dates, le lieu, l'âge requis ou les inscriptions.",
        "dates": f"Le camp a lieu du {start} au {end}.",  # Dates du camp.
        "location": f"Le camp se déroule à {camp.city}." if camp.city else  # Ville si elle est renseignée.
                    "Le lieu exact sera communiqué par l'organisateur.",  # Repli si la ville est absente.
        "age": (f"Ce camp est ouvert à partir de {camp.age} ans." if camp.age else "Ce camp est ouvert à tous les âges.")  # Âge minimum ou ouverture à tous.
               + (" Conditions : " + " ; ".join(m.label for m in camp.modalities) + "." if camp.modalities else ""),  # Ajoute les conditions (modalités) si elles existent.
        "places": f"Il reste {camp.remaining_places} place(s)." if camp.remaining_places > 0 else  # Places restantes.
                  "Ce camp est complet, désolé.",  # Message si plus aucune place.
        "registration": "Pour vous inscrire, remplissez le formulaire de cette page : "  # Explication de l'inscription.
                        "prénom, nom, email, puis confirmez votre participation.",
        "program": camp.description or "Le programme détaillé sera bientôt publié.",  # Description du camp, ou repli si vide.
        "human": "Vous pouvez joindre l'équipe via le formulaire de contact (hotline) de cette page. "  # Orientation vers le contact humain.
                 "Un organisateur vous répondra par email.",
    }
    return replies.get(  # Renvoie la réponse de l'intention demandée.
        intent,
        "Je n'ai pas compris. Je peux vous renseigner sur les dates, le lieu, l'âge requis, "  # Réponse de repli pour une intention inconnue.
        "les places restantes ou l'inscription.",
    )

def handle_message(db: Session, mongo: Database, slug: str, payload: ChatRequest) -> dict:  # Traite un message de visiteur et enregistre l'échange.
    camp = camp_service.get_public_camp(db, slug)  # Récupère le camp publié ; 404 s'il n'est pas publié.
    session_id = payload.session_id or str(uuid.uuid4())  # Réutilise la session du visiteur ou en crée une nouvelle.
    intent = detect_intent(payload.message)  # Détermine l'intention du message.
    reply = build_reply(intent, camp)  # Construit la réponse du bot.
    now = datetime.now(timezone.utc)  # Horodatage commun aux deux messages.

    try:
        # Une seule opération atomique :
        # - upsert=True crée le document au premier message ;
        # - $setOnInsert ne remplit ces champs qu'à la création ;
        # - $push ajoute les deux messages à la fin du tableau "messages".
        mongo[CONVERSATIONS].update_one(  # Crée ou met à jour le document de conversation.
            {"session_id": session_id, "camp_id": str(camp.id)},  # Filtre : la session pour ce camp.
            {
                "$setOnInsert": {"camp_slug": camp.slug, "created_at": now},  # Champs fixés à la création uniquement.
                "$set": {"updated_at": now},  # Date de dernière activité, mise à jour à chaque message.
                "$push": {"messages": {"$each": [  # Ajoute le message du visiteur puis la réponse du bot.
                    {"role": "visitor", "content": payload.message, "intent": intent, "at": now},
                    {"role": "bot", "content": reply, "intent": intent, "at": now},
                ]}},
            },
            upsert=True,  # Crée le document s'il n'existe pas encore.
        )
    except DuplicateKeyError as exc:  # Le session_id existe déjà pour un autre camp.
        # Ce session_id appartient déjà à la conversation d'un autre camp.
        raise ConflictError("Session de chat invalide pour ce camp.") from exc  # Renvoie un conflit.
    except PyMongoError as exc:  # Toute autre erreur MongoDB.
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc  # Renvoie un service indisponible.

    return {"session_id": session_id, "reply": reply, "intent": intent}  # Renvoie la session, la réponse et l'intention.

def list_conversations(db: Session, mongo: Database, camp_id: UUID, user: User, limit: int = 50) -> list[dict]:  # Liste les conversations d'un camp pour l'organisateur.
    camp_service.get_managed_camp(db, camp_id, user)  # contrôle d'accès dans PostgreSQL
    try:
        cursor = (  # Requête MongoDB sur les conversations du camp.
            mongo[CONVERSATIONS]
            .find({"camp_id": str(camp_id)}, {"_id": 0})  # projection : on exclut _id
            .sort("updated_at", DESCENDING)  # Les conversations les plus récentes en premier.
            .limit(limit)  # Nombre maximum de conversations renvoyées.
        )
        return list(cursor)  # Transforme le curseur en liste.
    except PyMongoError as exc:  # Erreur MongoDB.
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc

def stats(db: Session, mongo: Database, camp_id: UUID, user: User) -> dict:  # Statistiques des questions posées sur un camp.
    """
    Statistiques des questions posées, calculées par MongoDB (pipeline d'agrégation) :
    $match (ce camp) -> $unwind (un document par message) -> $match (messages visiteurs)
    -> $group (compte par intention) -> $sort -> $limit.
    """
    camp_service.get_managed_camp(db, camp_id, user)  # Vérifie les droits de gestion du camp.
    collection = mongo[CONVERSATIONS]  # Collection des conversations.
    pipeline = [  # Étapes d'agrégation MongoDB.
        {"$match": {"camp_id": str(camp_id)}},  # Garde uniquement les conversations de ce camp.
        {"$unwind": "$messages"},  # Un document par message au lieu d'un document par conversation.
        {"$match": {"messages.role": "visitor"}},  # Ne garde que les messages des visiteurs.
        {"$group": {"_id": "$messages.intent", "count": {"$sum": 1}}},  # Compte les messages par intention.
        {"$sort": {"count": -1, "_id": 1}},  # Intentions les plus fréquentes en premier, puis par nom.
    ]
    try:
        groups = list(collection.aggregate(pipeline))  # Exécute le pipeline.
        conversations = collection.count_documents({"camp_id": str(camp_id)})  # Nombre total de conversations du camp.
    except PyMongoError as exc:  # Erreur MongoDB.
        raise ServiceUnavailableError("Le chatbot est momentanément indisponible.") from exc

    return {
        "conversations": conversations,  # Nombre de conversations.
        "visitor_messages": sum(group["count"] for group in groups),  # Nombre total de messages visiteurs.
        "top_intents": [{"intent": group["_id"], "count": group["count"]} for group in groups[:5]],  # Les cinq intentions les plus fréquentes.
    }