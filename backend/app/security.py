"""
Sécurité : hachage de mot de passe et gestion des tokens JWT.

- Hachage : `passlib[bcrypt]` — algorithme lent par design (résistant au bruteforce).
- JWT : `python-jose` — signature HS256 avec la clé `SECRET_KEY`.
"""
# On importe datetime (date et heure), timedelta (durée) et timezone (fuseau horaire)
from datetime import datetime, timedelta, timezone

# On importe JWTError (erreur de token invalide) et jwt (encodage/décodage des tokens)
from jose import JWTError, jwt
# On importe CryptContext, l'outil de passlib qui gère le hachage des mots de passe
from passlib.context import CryptContext

# On importe les paramètres de l'application (clé secrète, algorithme, durée du token)
from app.config import settings

# Contexte de hachage : bcrypt est l'algorithme recommandé pour les mots de passe.
# On crée le contexte de hachage en n'autorisant que bcrypt ; "auto" marque les anciens schémas comme obsolètes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Hachage de mot de passe
# ---------------------------------------------------------------------------
# Fonction qui prend un mot de passe en clair et retourne son hachage sous forme de texte
def hash_password(password: str) -> str:
    """Hache un mot de passe en clair.

    bcrypt ajoute automatiquement un "salt" aléatoire, donc deux hachages
    du même mot de passe donnent des résultats différents.
    """
    # On génère et on retourne le hachage bcrypt du mot de passe (salt aléatoire inclus)
    return pwd_context.hash(password)


# Fonction qui compare un mot de passe en clair à un hachage et retourne True ou False
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond à son hachage."""
    # On vérifie la correspondance en réutilisant le salt contenu dans le hachage stocké
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
# Début de la fonction qui crée un token d'accès
def create_access_token(
    # Paramètre : identifiant de l'utilisateur, sous forme de texte
    subject: str,
    # Paramètre optionnel : durée de validité du token (None par défaut)
    expires_delta: timedelta | None = None,
# La fonction retourne le token sous forme de texte
) -> str:
    """Crée un token JWT signé.

    Args:
        subject: identifiant du sujet (ici, l'UUID de l'utilisateur en str).
        expires_delta: durée de validité. Si None, utilise la config par défaut.

    Returns:
        Le token JWT encodé (str).
    """
    # Si aucune durée n'a été fournie par l'appelant...
    if expires_delta is None:
        # ...on construit la durée à partir du nombre de minutes défini dans la configuration
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    # On récupère la date et l'heure actuelles en UTC
    now = datetime.now(timezone.utc)
    # On construit le contenu (payload) du token
    payload = {
        # "sub" : le sujet du token, c'est-à-dire l'utilisateur concerné
        "sub": subject,
        # "iat" (issued at) : date de création du token
        "iat": now,
        # "exp" : date d'expiration, égale à maintenant + la durée de validité
        "exp": now + expires_delta,
    # Fin du dictionnaire payload
    }
    # On signe le payload avec la clé secrète et l'algorithme configuré, puis on retourne le token
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# Fonction qui décode un token et retourne l'UUID de l'utilisateur, ou None si le token est invalide
def decode_access_token(token: str) -> str | None:
    """Décode un token JWT et retourne le `sub` (UUID utilisateur).

    Returns:
        L'UUID en str si le token est valide, None sinon.
    """
    # On tente le décodage : si une erreur survient, elle sera interceptée plus bas
    try:
        # On décode le token ; la signature et la date d'expiration sont vérifiées automatiquement
        payload = jwt.decode(
            # Le token à décoder
            token,
            # La clé secrète servant à vérifier la signature
            settings.secret_key,
            # Liste des algorithmes acceptés (on n'autorise que celui de la configuration)
            algorithms=[settings.algorithm],
        # Fin de l'appel à jwt.decode
        )
        # On retourne l'identifiant de l'utilisateur stocké dans "sub" (None s'il est absent)
        return payload.get("sub")
    # Si le token est invalide, expiré, falsifié ou mal formé...
    except JWTError:
        # ...on retourne None pour signaler l'échec sans lever d'erreur
        return None
