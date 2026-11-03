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
import base64
import io
from uuid import UUID

import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import TWO_FACTOR_SCOPE, decode_token
from app.models import User, UserStatus

ISSUER = "CampOrga"


class InvalidTwoFactorError(Exception):
    """Jeton temporaire ou code refusé lors de la connexion (traduit en 401)."""


def _verify(user: User, code: str) -> bool:
    if not user.totp_secret:
        return False
    # valid_window=1 : on accepte aussi le code précédent/suivant (horloges décalées).
    return pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)


def setup(db: Session, user: User) -> dict:
    if user.is_2fa_enabled:
        # Sinon, un nouvel appel écraserait le secret d'une 2FA déjà active.
        raise ConflictError("La double authentification est déjà activée.")
    secret = pyotp.random_base32()
    otpauth_url = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=ISSUER)

    image = qrcode.make(otpauth_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    user.totp_secret = secret
    db.commit()
    return {
        "secret": secret,
        "otpauth_url": otpauth_url,
        "qr_code_base64": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(),
    }


def enable(db: Session, user: User, code: str) -> None:
    if user.is_2fa_enabled:
        raise ConflictError("La double authentification est déjà activée.")
    if not _verify(user, code):
        raise ValidationError("Code de vérification invalide.")
    user.is_2fa_enabled = True
    db.commit()


def disable(db: Session, user: User, code: str) -> None:
    if not user.is_2fa_enabled:
        raise ConflictError("La double authentification n'est pas activée.")
    if not _verify(user, code):
        raise ValidationError("Code de vérification invalide.")
    user.is_2fa_enabled = False
    user.totp_secret = None
    db.commit()


def verify_login(db: Session, temp_token: str, code: str) -> User:
    """Étape 2 de la connexion : vérifie le jeton temporaire puis le code."""
    subject = decode_token(temp_token, TWO_FACTOR_SCOPE)
    try:
        user = db.get(User, UUID(subject or ""))
    except ValueError:
        user = None
    if user is None or user.status != UserStatus.ACTIVE or not user.is_2fa_enabled:
        raise InvalidTwoFactorError("Session de connexion expirée, recommencez.")
    if not _verify(user, code):
        raise InvalidTwoFactorError("Code de vérification invalide.")
    return user
