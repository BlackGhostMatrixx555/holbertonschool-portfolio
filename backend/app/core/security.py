"""
Outils de sécurité : hachage des mots de passe et jetons JWT.

- Les mots de passe ne sont jamais stockés en clair : on stocke uniquement
  leur empreinte bcrypt (algorithme lent et salé, résistant au brute force).
- Les jetons JWT sont signés avec SECRET_KEY (HS256). Le serveur n'a rien à
  stocker : il vérifie la signature et la date d'expiration à chaque requête.
- Chaque jeton porte une "portée" (claim `scope`) :
    * "access"      : jeton de session normal ;
    * "2fa_pending" : jeton temporaire (5 min) délivré après le mot de passe,
                      quand la double authentification est activée.
  Un jeton "2fa_pending" n'ouvre AUCUNE route protégée : il sert uniquement
  à valider le code à 6 chiffres. Sans cette distinction, la 2FA pourrait
  être contournée en utilisant directement le jeton temporaire.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_SCOPE = "access"
TWO_FACTOR_SCOPE = "2fa_pending"
TWO_FACTOR_TOKEN_MINUTES = 5


def hash_password(password: str) -> str:
    """Retourne l'empreinte bcrypt d'un mot de passe."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare un mot de passe saisi avec l'empreinte stockée."""
    return pwd_context.verify(plain_password, hashed_password)


def _encode(subject: Any, scope: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(subject), "scope": scope, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """Crée le jeton de session (portée "access")."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _encode(subject, ACCESS_SCOPE, expires_delta)


def create_two_factor_token(subject: Any) -> str:
    """Crée le jeton temporaire de l'étape 2 de la connexion (2FA)."""
    return _encode(subject, TWO_FACTOR_SCOPE, timedelta(minutes=TWO_FACTOR_TOKEN_MINUTES))


def decode_token(token: str, expected_scope: str) -> str | None:
    """
    Vérifie signature, expiration ET portée du jeton ; retourne le `sub` ou None.

    Les jetons émis avant l'ajout de la portée n'ont pas de claim `scope` :
    ce sont forcément des jetons de session, on les traite comme "access".
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if payload.get("scope", ACCESS_SCOPE) != expected_scope:
        return None
    return payload.get("sub")
