"""
Connexion à MongoDB (base NoSQL orientée documents).

Pourquoi MongoDB pour le chatbot ?
Une conversation est un document naturellement imbriqué : une session
contient une liste de messages de longueur variable. En SQL, il faudrait
deux tables et une jointure à chaque lecture ; dans MongoDB, toute la
conversation est un seul document lu ou complété en une opération.
Les données critiques (comptes, camps, inscriptions) restent dans PostgreSQL,
qui garantit l'intégrité relationnelle (clés étrangères, transactions).
"""  # Docstring du module : justification du choix de MongoDB pour le chatbot.
from datetime import timedelta  # Permet de convertir une durée en secondes (utilisé pour le TTL).

from pymongo import ASCENDING, DESCENDING, MongoClient  # Constantes de tri et client MongoDB.
from pymongo.database import Database  # Type représentant une base MongoDB, utilisé pour les annotations.

from app.core.config import settings  # Configuration de l'application (URL MongoDB, durée de rétention...).

CONVERSATIONS = "chat_conversations"  # Nom de la collection stockant les conversations du chatbot.
VERIFICATION_CODES = "verification_codes"  # Nom de la collection stockant les codes de vérification.

_client: MongoClient | None = None  # Client MongoDB partagé, initialisé à None (variable privée au module).

def get_client() -> MongoClient:  # Retourne le client MongoDB, en le créant au premier appel.
    """Crée le client une seule fois (il gère lui-même un pool de connexions)."""  # Docstring : création unique du client.
    global _client  # Indique qu'on modifie la variable globale _client.
    if _client is None:  # Vérifie que le client n'a pas encore été créé.
        # serverSelectionTimeoutMS : on échoue vite si MongoDB est arrêté,
        # au lieu de bloquer la requête HTTP 30 secondes.
        _client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000, tz_aware=True)  # Crée le client ; timeout de 2 s ; tz_aware renvoie des dates avec fuseau horaire.
    return _client  # Retourne le client (créé ou existant).

def get_mongo_db() -> Database:  # Dépendance FastAPI qui fournit la base MongoDB.
    """Dépendance FastAPI : fournit la base MongoDB (remplacée dans les tests)."""  # Docstring : peut être remplacée par un double dans les tests.
    return get_client()[settings.MONGO_DB_NAME]  # Sélectionne la base nommée dans la configuration.

def ensure_indexes(db: Database) -> None:  # Crée les index nécessaires ; ne retourne rien.
    """
    Crée les index MongoDB (opération idempotente).

    - session_id unique : une conversation = une session de navigateur.
    - (camp_id, updated_at) : liste rapide des conversations d'un camp, récentes d'abord.
    - Index TTL sur updated_at : MongoDB supprime automatiquement les
      conversations inactives depuis CHAT_RETENTION_DAYS jours (RGPD).
    """  # Docstring : rôle de chaque index.
    collection = db[CONVERSATIONS]  # Sélectionne la collection des conversations.
    collection.create_index([("session_id", ASCENDING)], unique=True)  # Index unique sur session_id : pas deux conversations pour une même session.
    collection.create_index([("camp_id", ASCENDING), ("updated_at", DESCENDING)])  # Index composé pour lister les conversations d'un camp, les plus récentes d'abord.
    collection.create_index(  # Index TTL : MongoDB supprime les documents automatiquement.
        [("updated_at", ASCENDING)],  # Champ de date utilisé pour calculer l'expiration.
        name="updated_at_ttl",  # Nom explicite de l'index.
        expireAfterSeconds=int(timedelta(days=settings.CHAT_RETENTION_DAYS).total_seconds()),  # Durée de rétention convertie en secondes.
    )

    # Codes de vérification (email / SMS) : un par utilisateur, supprimés
    # automatiquement à leur date d'expiration (expireAfterSeconds=0).
    codes = db[VERIFICATION_CODES]  # Sélectionne la collection des codes de vérification.
    codes.create_index([("user_id", ASCENDING)], unique=True)  # Un seul code actif par utilisateur.
    codes.create_index([("expires_at", ASCENDING)], name="expires_at_ttl", expireAfterSeconds=0)  # TTL : supprime le document à l'heure indiquée dans expires_at.