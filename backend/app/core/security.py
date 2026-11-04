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
"""  # Docstring du module : hachage, JWT et distinction des portées de jetons.
from datetime import datetime, timedelta, timezone  # Dates, durées et fuseau UTC pour les dates d'émission et d'expiration.
from typing import Any  # Type générique pour accepter n'importe quel identifiant (sujet du jeton).

from jose import JWTError, jwt  # Bibliothèque JWT : jwt pour encoder/décoder, JWTError pour les jetons invalides.
from passlib.context import CryptContext  # Gestionnaire de hachage de mots de passe.

from app.core.config import settings  # Configuration de l'application, contient SECRET_KEY et les durées.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Contexte de hachage utilisant bcrypt ; remet à niveau automatiquement les anciens hachages.

ALGORITHM = "HS256"  # Algorithme de signature des jetons (HMAC avec SHA-256 et clé secrète).
ACCESS_SCOPE = "access"  # Portée d'un jeton de session normal.
TWO_FACTOR_SCOPE = "2fa_pending"  # Portée d'un jeton temporaire de l'étape 2FA.
TWO_FACTOR_TOKEN_MINUTES = 5  # Durée de validité du jeton 2FA, en minutes.

def hash_password(password: str) -> str:  # Transforme un mot de passe en empreinte.
    """Retourne l'empreinte bcrypt d'un mot de passe."""  # Docstring : rôle de la fonction.
    return pwd_context.hash(password)  # Calcule et retourne le hachage bcrypt (avec sel intégré).

def verify_password(plain_password: str, hashed_password: str) -> bool:  # Vérifie un mot de passe saisi.
    """Compare un mot de passe saisi avec l'empreinte stockée."""  # Docstring : rôle de la fonction.
    return pwd_context.verify(plain_password, hashed_password)  # Retourne True si le mot de passe correspond au hachage.

def _encode(subject: Any, scope: str, expires_delta: timedelta) -> str:  # Fonction interne qui fabrique un jeton signé (préfixe _ : usage privé).
    now = datetime.now(timezone.utc)  # Date et heure actuelles en UTC.
    payload = {"sub": str(subject), "scope": scope, "iat": now, "exp": now + expires_delta}  # Contenu du jeton : sujet, portée, date d'émission et d'expiration.
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)  # Signe le contenu avec la clé secrète et retourne le jeton.

def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:  # Crée le jeton de session.
    """Crée le jeton de session (portée "access")."""  # Docstring : portée du jeton produit.
    if expires_delta is None:  # Si aucune durée n'est précisée...
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)  # ...on utilise la durée par défaut de la configuration.
    return _encode(subject, ACCESS_SCOPE, expires_delta)  # Délègue la création du jeton avec la portée "access".

def create_two_factor_token(subject: Any) -> str:  # Crée le jeton temporaire de la 2FA.
    """Crée le jeton temporaire de l'étape 2 de la connexion (2FA)."""  # Docstring : usage du jeton.
    return _encode(subject, TWO_FACTOR_SCOPE, timedelta(minutes=TWO_FACTOR_TOKEN_MINUTES))  # Jeton de portée "2fa_pending" valable 5 minutes.

def decode_token(token: str, expected_scope: str) -> str | None:  # Vérifie un jeton et retourne l'identifiant du sujet.
    """
    Vérifie signature, expiration ET portée du jeton ; retourne le `sub` ou None.

    Les jetons émis avant l'ajout de la portée n'ont pas de claim `scope` :
    ce sont forcément des jetons de session, on les traite comme "access".
    """  # Docstring : contrôles effectués et traitement des anciens jetons.
    try:  # Tente de décoder le jeton ; une exception signifie qu'il est invalide.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])  # Vérifie la signature et l'expiration, puis retourne le contenu.
    except JWTError:  # Jeton falsifié, expiré ou mal formé.
        return None  # Le jeton est rejeté.
    if payload.get("scope", ACCESS_SCOPE) != expected_scope:  # Lit la portée ; un jeton sans portée est considéré comme "access" ; refuse si la portée ne correspond pas.
        return None  # Mauvaise portée : par exemple un jeton 2FA utilisé comme jeton de session.
    return payload.get("sub")  # Retourne l'identifiant de l'utilisateur contenu dans le jeton.