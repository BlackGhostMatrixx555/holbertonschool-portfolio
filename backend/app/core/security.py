"""
Outils de sécurité : hachage des mots de passe et jetons JWT.

- Les mots de passe ne sont jamais stockés en clair : on stocke uniquement
  leur empreinte bcrypt (algorithme lent et salé, résistant au brute force).
- Les jetons JWT sont signés avec SECRET_KEY (HS256). Le serveur n'a rien à
  stocker : il vérifie la signature et la date d'expiration à chaque requête.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Retourne l'empreinte bcrypt d'un mot de passe."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare un mot de passe saisi avec l'empreinte stockée."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """
    Crée un jeton JWT signé.

    `subject` est l'identifiant de l'utilisateur (claim "sub").
    `exp` est calculé en UTC avec un datetime "aware" : datetime.utcnow()
    est déprécié depuis Python 3.12.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
