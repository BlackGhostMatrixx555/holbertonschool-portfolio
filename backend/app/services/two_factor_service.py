"""
Double authentification par code TOTP (apport de tete-work).

TOTP = "Time-based One-Time Password" (RFC 6238) : le serveur et l'application
du téléphone (Google Authenticator, Authy...) partagent un secret, et calculent
chacun un code à 6 chiffres qui change toutes les 30 secondes.

Déroulé :
1. setup  : on génère un secret et un QR code ; la 2FA n'est pas encore active.
2. enable : l'utilisateur saisit un premier code, preuve qu'il a bien scanné.
3. login  : mot de passe -> jeton temporaire -> code -> jeton de session.
4. disable: exige un code valide (sinon, un vol de session suffirait à la retirer).
"""
import base64  # Encodage en base64, utilisé pour transmettre l'image du QR code sous forme de texte.
import io  # Flux en mémoire, pour générer l'image sans écrire de fichier sur le disque.
from uuid import UUID  # Type des identifiants des utilisateurs.

import pyotp  # Bibliothèque de calcul des codes TOTP.
import qrcode  # Bibliothèque de génération de QR codes.
from sqlalchemy.orm import Session  # Session SQLAlchemy pour interroger et modifier la base.

from app.core.exceptions import ConflictError, ValidationError  # Erreurs métier : conflit d'état et donnée invalide.
from app.core.security import TWO_FACTOR_SCOPE, decode_token  # Constante identifiant les jetons temporaires 2FA, et fonction de décodage des jetons.
from app.models import User, UserStatus  # Modèle utilisateur et statuts possibles.

ISSUER = "CampOrga"  # Nom affiché dans l'application d'authentification à côté du code.

class InvalidTwoFactorError(Exception):  # Exception levée pendant la connexion en deux étapes.
    """Jeton temporaire ou code refusé lors de la connexion (traduit en 401)."""

def _verify(user: User, code: str) -> bool:  # Fonction privée : vérifie un code TOTP pour un utilisateur.
    if not user.totp_secret:  # Pas de secret enregistré : aucun code ne peut être valide.
        return False
    # valid_window=1 : on accepte aussi le code précédent/suivant (horloges décalées).
    return pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)  # Compare le code saisi aux codes attendus pour l'instant présent.

def setup(db: Session, user: User) -> dict:  # Étape 1 : prépare l'activation de la 2FA.
    if user.is_2fa_enabled:  # La 2FA est déjà active.
        # Sinon, un nouvel appel écraserait le secret d'une 2FA déjà active.
        raise ConflictError("La double authentification est déjà activée.")
    secret = pyotp.random_base32()  # Génère un secret aléatoire, encodé en base32 (lisible par les applications).
    otpauth_url = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=ISSUER)  # URL standard « otpauth:// » contenant le secret, le compte et l'émetteur.

    image = qrcode.make(otpauth_url)  # Génère le QR code qui contient cette URL.
    buffer = io.BytesIO()  # Tampon en mémoire.
    image.save(buffer, format="PNG")  # Écrit l'image PNG dans le tampon.

    user.totp_secret = secret  # Enregistre le secret ; la 2FA reste inactive tant que le premier code n'est pas validé.
    db.commit()
    return {
        "secret": secret,  # Secret en clair, pour une saisie manuelle si le scan est impossible.
        "otpauth_url": otpauth_url,
        "qr_code_base64": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(),  # Image prête à être affichée directement dans une balise <img>.
    }

def enable(db: Session, user: User, code: str) -> None:  # Étape 2 : active la 2FA après vérification d'un premier code.
    if user.is_2fa_enabled:  # Déjà active : rien à faire.
        raise ConflictError("La double authentification est déjà activée.")
    if not _verify(user, code):  # Le code saisi ne correspond pas : l'utilisateur n'a probablement pas scanné le QR code.
        raise ValidationError("Code de vérification invalide.")
    user.is_2fa_enabled = True  # Active la 2FA.
    db.commit()

def disable(db: Session, user: User, code: str) -> None:  # Désactive la 2FA, avec confirmation par code.
    if not user.is_2fa_enabled:  # Déjà désactivée.
        raise ConflictError("La double authentification n'est pas activée.")
    if not _verify(user, code):  # Sans code valide, la désactivation est refusée.
        raise ValidationError("Code de vérification invalide.")
    user.is_2fa_enabled = False  # Désactive la 2FA.
    user.totp_secret = None  # Efface le secret, qui ne doit plus servir.
    db.commit()

def verify_login(db: Session, temp_token: str, code: str) -> User:  # Étape 2 de la connexion.
    """Étape 2 de la connexion : vérifie le jeton temporaire puis le code."""
    subject = decode_token(temp_token, TWO_FACTOR_SCOPE)  # Décode le jeton temporaire ; il doit avoir le bon « scope ».
    try:
        user = db.get(User, UUID(subject or ""))  # Convertit l'identifiant en UUID et recherche l'utilisateur.
    except ValueError:  # Identifiant mal formé.
        user = None
    if user is None or user.status != UserStatus.ACTIVE or not user.is_2fa_enabled:  # Utilisateur absent, non actif, ou sans 2FA.
        raise InvalidTwoFactorError("Session de connexion expirée, recommencez.")  # Message volontairement vague.
    if not _verify(user, code):  # Code TOTP incorrect.
        raise InvalidTwoFactorError("Code de vérification invalide.")
    return user  # Connexion en deux étapes réussie.