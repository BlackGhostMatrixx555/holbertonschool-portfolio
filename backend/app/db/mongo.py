"""
Connexion à MongoDB (base NoSQL orientée documents).

Pourquoi MongoDB pour le chatbot ?
Une conversation est un document naturellement imbriqué : une session
contient une liste de messages de longueur variable. En SQL, il faudrait
deux tables et une jointure à chaque lecture ; dans MongoDB, toute la
conversation est un seul document lu ou complété en une opération.
Les données critiques (comptes, camps, inscriptions) restent dans PostgreSQL,
qui garantit l'intégrité relationnelle (clés étrangères, transactions).
"""
from datetime import timedelta

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from app.core.config import settings

CONVERSATIONS = "chat_conversations"

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Crée le client une seule fois (il gère lui-même un pool de connexions)."""
    global _client
    if _client is None:
        # serverSelectionTimeoutMS : on échoue vite si MongoDB est arrêté,
        # au lieu de bloquer la requête HTTP 30 secondes.
        _client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000, tz_aware=True)
    return _client


def get_mongo_db() -> Database:
    """Dépendance FastAPI : fournit la base MongoDB (remplacée dans les tests)."""
    return get_client()[settings.MONGO_DB_NAME]


def ensure_indexes(db: Database) -> None:
    """
    Crée les index de la collection des conversations (opération idempotente).

    - session_id unique : une conversation = une session de navigateur.
    - (camp_id, updated_at) : liste rapide des conversations d'un camp, récentes d'abord.
    - Index TTL sur updated_at : MongoDB supprime automatiquement les
      conversations inactives depuis CHAT_RETENTION_DAYS jours (RGPD).
    """
    collection = db[CONVERSATIONS]
    collection.create_index([("session_id", ASCENDING)], unique=True)
    collection.create_index([("camp_id", ASCENDING), ("updated_at", DESCENDING)])
    collection.create_index(
        [("updated_at", ASCENDING)],
        name="updated_at_ttl",
        expireAfterSeconds=int(timedelta(days=settings.CHAT_RETENTION_DAYS).total_seconds()),
    )
