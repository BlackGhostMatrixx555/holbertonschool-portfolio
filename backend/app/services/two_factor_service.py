"""
Service métier pour la double authentification (TOTP).
"""
import base64
import io
import uuid
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User


class TwoFactorService:
    def __init__(self, db: Session):
        self.db = db

    def generate_secret(self, user: User) -> dict:
        """Génère un secret TOTP, un QR code et stocke le secret en attente."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        otpauth_url = totp.provisioning_uri(name=user.email, issuer_name="CampOrga")

        qr = qrcode.make(otpauth_url)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        user.totp_secret = secret
        user.is_2fa_enabled = False
        self.db.commit()
        self.db.refresh(user)

        return {
            "secret": secret,
            "otpauth_url": otpauth_url,
            "qr_code_base64": f"data:image/png;base64,{qr_base64}",
        }

    def verify_code(self, user: User, code: str) -> bool:
        """Vérifie qu'un code TOTP est valide."""
        if not user.totp_secret:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)

    def enable_2fa(self, user: User, code: str) -> bool:
        """Active la 2FA si le code fourni est valide."""
        if self.verify_code(user, code):
            user.is_2fa_enabled = True
            self.db.commit()
            return True
        return False

    def disable_2fa(self, user: User):
        """Désactive la 2FA (supprime le secret)."""
        user.is_2fa_enabled = False
        user.totp_secret = None
        self.db.commit()

    def create_temp_token(self, user: User) -> str:
        """Crée un token temporaire (5 min) pour la validation 2FA."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "scope": "2fa_pending",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    def verify_temp_token(self, token: str) -> User | None:
        """Décode un token temporaire et renvoie l'utilisateur associé."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("scope") != "2fa_pending":
                return None
            user_id = payload.get("sub")
            return self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        except (JWTError, ValueError):
            return None
