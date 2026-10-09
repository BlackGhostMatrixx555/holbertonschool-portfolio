"""
Sécurité : hachage de mot de passe et gestion des tokens JWT.

- Hachage : `passlib[bcrypt]` — algorithme lent par design (résistant au bruteforce).
- JWT : `python-jose` — signature HS256 avec la clé `SECRET_KEY`.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Contexte de hachage : bcrypt est l'algorithme recommandé pour les mots de passe.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Hachage de mot de passe
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hache un mot de passe en clair.

    bcrypt ajoute automatiquement un "salt" aléatoire, donc deux hachages
    du même mot de passe donnent des résultats différents.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond à son hachage."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Crée un token JWT signé.

    Args:
        subject: identifiant du sujet (ici, l'UUID de l'utilisateur en str).
        expires_delta: durée de validité. Si None, utilise la config par défaut.

    Returns:
        Le token JWT encodé (str).
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """Décode un token JWT et retourne le `sub` (UUID utilisateur).

    Returns:
        L'UUID en str si le token est valide, None sinon.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload.get("sub")
    except JWTError:
        return None
