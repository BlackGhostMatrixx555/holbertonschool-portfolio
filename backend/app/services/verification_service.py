"""
Service de vérification par SMS et Email (mode Mock pour le MVP).
"""
import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import User

# Stockage en mémoire des codes (en prod : Redis avec TTL)
# Format : { "user_id": { "code": "123456", "expires_at": datetime, "method": "sms" } }
_verification_codes: dict[str, dict] = {}


class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_code(self) -> str:
        """Génère un code à 6 chiffres."""
        return "".join(random.choices(string.digits, k=6))

    def send_sms_code(self, user: User) -> str:
        """Génère et envoie un code par SMS (Mock)."""
        if not user.phone_number:
            raise ValueError("Aucun numéro de téléphone associé à ce compte.")

        code = self._generate_code()
        _verification_codes[str(user.id)] = {
            "code": code,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "method": "sms",
        }

        # MOCK : on affiche le code dans les logs du serveur
        print(f"📱 [MOCK SMS] Code pour {user.phone_number} : {code}")

        return code

    def send_email_code(self, user: User) -> str:
        """Génère et envoie un code par Email (Mock)."""
        code = self._generate_code()
        _verification_codes[str(user.id)] = {
            "code": code,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "method": "email",
        }

        print(f"📧 [MOCK EMAIL] Code pour {user.email} : {code}")

        return code

    def verify_code(self, user: User, code: str) -> bool:
        """Vérifie si le code est valide et non expiré."""
        user_data = _verification_codes.get(str(user.id))
        if not user_data:
            return False

        if user_data["expires_at"] < datetime.utcnow():
            del _verification_codes[str(user.id)]
            return False

        if user_data["code"] == code:
            del _verification_codes[str(user.id)]  # Consomme le code
            return True

        return False
