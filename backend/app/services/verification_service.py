"""
Vérification de l'email ou du téléphone par code à 6 chiffres (apport de tete-work).

L'envoi est simulé pour le MVP (le code est écrit dans les logs du serveur,
et renvoyé dans la réponse UNIQUEMENT en développement).

Les codes sont stockés dans MongoDB, collection "verification_codes" :
- l'index TTL sur `expires_at` fait supprimer les codes périmés par MongoDB ;
- on ne stocke que l'empreinte SHA-256 du code, jamais le code lui-même ;
- le nombre d'essais est limité, pour empêcher de deviner le code par force brute.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.db.mongo import VERIFICATION_CODES
from app.models import User

logger = logging.getLogger("camporga.verification")


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def send_code(mongo: Database, user: User, method: str) -> dict:
    """Génère un code, l'enregistre (empreinte) et simule son envoi."""
    if method == "sms" and not user.phone_number:
        raise ValidationError("Aucun numéro de téléphone n'est associé à ce compte.")

    # `secrets` (et non `random`) : générateur cryptographique, imprévisible.
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)
    try:
        # Un seul code valide à la fois par utilisateur : le nouveau remplace l'ancien.
        mongo[VERIFICATION_CODES].replace_one(
            {"user_id": str(user.id)},
            {
                "user_id": str(user.id),
                "method": method,
                "code_hash": _hash(code),
                "attempts": 0,
                "created_at": now,
                "expires_at": now + timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES),
            },
            upsert=True,
        )
    except PyMongoError as exc:
        raise ServiceUnavailableError("La vérification est momentanément indisponible.") from exc

    destination = user.phone_number if method == "sms" else user.email
    logger.info("[ENVOI SIMULÉ %s] Code pour %s : %s", method.upper(), destination, code)
    return {
        "message": "Code envoyé par SMS." if method == "sms" else "Code envoyé par email.",
        "debug_code": code if settings.is_development else None,
    }


def check_code(mongo: Database, user: User, code: str) -> None:
    """Vérifie le code ; il est consommé (supprimé) dès qu'il est validé."""
    collection = mongo[VERIFICATION_CODES]
    try:
        entry = collection.find_one({"user_id": str(user.id)})
        expired = entry is not None and entry["expires_at"] < datetime.now(timezone.utc)
        if entry is None or expired or entry["attempts"] >= settings.VERIFICATION_MAX_ATTEMPTS:
            collection.delete_one({"user_id": str(user.id)})
            raise ValidationError("Code invalide ou expiré. Demandez un nouveau code.")

        # compare_digest : comparaison en temps constant (pas de fuite par le temps de réponse).
        if not secrets.compare_digest(entry["code_hash"], _hash(code)):
            collection.update_one({"user_id": str(user.id)}, {"$inc": {"attempts": 1}})
            raise ValidationError("Code invalide.")

        collection.delete_one({"user_id": str(user.id)})
    except PyMongoError as exc:
        raise ServiceUnavailableError("La vérification est momentanément indisponible.") from exc
