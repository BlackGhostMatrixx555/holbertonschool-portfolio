"""
Vérification de l'email ou du téléphone par code à 6 chiffres (apport de tete-work).

L'envoi est simulé pour le MVP (le code est écrit dans les logs du serveur,
et renvoyé dans la réponse UNIQUEMENT en développement).

Les codes sont stockés dans MongoDB, collection "verification_codes" :
- l'index TTL sur `expires_at` fait supprimer les codes périmés par MongoDB ;
- on ne stocke que l'empreinte SHA-256 du code, jamais le code lui-même ;
- le nombre d'essais est limité, pour empêcher de deviner le code par force brute.
"""
import hashlib  # Module standard pour calculer des empreintes (hash) cryptographiques.
import logging  # Module standard de journalisation (logs).
import secrets  # Générateur de nombres aléatoires cryptographiquement sûrs.
from datetime import datetime, timedelta, timezone  # Dates, durées, et fuseau horaire UTC.

from pymongo.database import Database  # Type représentant une base MongoDB.
from pymongo.errors import PyMongoError  # Classe de base des erreurs du driver MongoDB.

from app.core.config import settings  # Configuration globale (durée de validité, nombre d'essais, mode développement).
from app.core.exceptions import ServiceUnavailableError, ValidationError  # Erreurs métier : service indisponible et donnée invalide.
from app.db.mongo import VERIFICATION_CODES  # Nom de la collection MongoDB des codes.
from app.models import User  # Modèle utilisateur.

logger = logging.getLogger("camporga.verification")  # Logger dédié à la vérification ; ses messages portent ce nom dans les logs.

def _hash(code: str) -> str:  # Fonction privée (préfixe _) : calcule l'empreinte SHA-256 d'un code.
    return hashlib.sha256(code.encode()).hexdigest()  # Encode le code en octets, calcule le hash, renvoie-le en texte hexadécimal.

def send_code(mongo: Database, user: User, method: str) -> dict:  # Génère un code, l'enregistre et simule son envoi.
    """Génère un code, l'enregistre (empreinte) et simule son envoi."""
    if method == "sms" and not user.phone_number:  # Envoi par SMS demandé mais aucun numéro enregistré.
        raise ValidationError("Aucun numéro de téléphone n'est associé à ce compte.")  # Refuse la demande.

    # `secrets` (et non `random`) : générateur cryptographique, imprévisible.
    code = f"{secrets.randbelow(1_000_000):06d}"  # Tire un entier entre 0 et 999999, et le complète à 6 chiffres (ex. « 004821 »).
    now = datetime.now(timezone.utc)  # Date et heure actuelles en UTC, référence pour l'expiration.
    try:
        # Un seul code valide à la fois par utilisateur : le nouveau remplace l'ancien.
        mongo[VERIFICATION_CODES].replace_one(  # Remplace le document existant de cet utilisateur, ou en crée un.
            {"user_id": str(user.id)},  # Filtre : le document de cet utilisateur.
            {  # Nouveau document à enregistrer.
                "user_id": str(user.id),  # Identifiant de l'utilisateur, converti en texte.
                "method": method,  # Canal d'envoi : « sms » ou « email ».
                "code_hash": _hash(code),  # Empreinte du code, jamais le code en clair.
                "attempts": 0,  # Compteur d'essais échoués, remis à zéro pour un nouveau code.
                "created_at": now,  # Date de création du code.
                "expires_at": now + timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES),  # Date d'expiration : maintenant plus la durée de validité configurée.
            },
            upsert=True,  # Si aucun document ne correspond, en crée un.
        )
    except PyMongoError as exc:  # MongoDB est injoignable ou l'écriture a échoué.
        raise ServiceUnavailableError("La vérification est momentanément indisponible.") from exc  # Renvoie une erreur de service indisponible ; « from exc » garde l'erreur d'origine.

    destination = user.phone_number if method == "sms" else user.email  # Destinataire réel : le numéro pour un SMS, l'email sinon.
    logger.info("[ENVOI SIMULÉ %s] Code pour %s : %s", method.upper(), destination, code)  # Écrit le code dans les logs, car l'envoi réel est simulé.
    return {  # Réponse renvoyée au client.
        "message": "Code envoyé par SMS." if method == "sms" else "Code envoyé par email.",  # Message adapté au canal choisi.
        "debug_code": code if settings.is_development else None,  # Le code n'est renvoyé au client qu'en développement, jamais en production.
    }

def check_code(mongo: Database, user: User, code: str) -> None:  # Vérifie le code saisi ; ne renvoie rien en cas de succès.
    """Vérifie le code ; il est consommé (supprimé) dès qu'il est validé."""
    collection = mongo[VERIFICATION_CODES]  # Raccourci vers la collection des codes.
    try:
        entry = collection.find_one({"user_id": str(user.id)})  # Cherche le code de cet utilisateur (None si absent).
        expired = entry is not None and entry["expires_at"] < datetime.now(timezone.utc)  # Vrai si un code existe et que sa date d'expiration est dépassée.
        if entry is None or expired or entry["attempts"] >= settings.VERIFICATION_MAX_ATTEMPTS:  # Aucun code, code expiré, ou trop d'essais.
            collection.delete_one({"user_id": str(user.id)})  # Supprime le code restant pour forcer une nouvelle demande.
            raise ValidationError("Code invalide ou expiré. Demandez un nouveau code.")  # Refuse la vérification.

        # compare_digest : comparaison en temps constant (pas de fuite par le temps de réponse).
        if not secrets.compare_digest(entry["code_hash"], _hash(code)):  # Compare les empreintes sans révéler, par la durée, où elles diffèrent.
            collection.update_one({"user_id": str(user.id)}, {"$inc": {"attempts": 1}})  # Incrémente le compteur d'essais échoués de 1.
            raise ValidationError("Code invalide.")  # Refuse le code saisi.

        collection.delete_one({"user_id": str(user.id)})  # Code correct : on le supprime pour qu'il ne puisse pas être réutilisé.
    except PyMongoError as exc:  # MongoDB est injoignable ou une opération a échoué.
        raise ServiceUnavailableError("La vérification est momentanément indisponible.") from exc  # Renvoie une erreur de service indisponible.