"""
Dépendances FastAPI partagées.

`get_current_user` : lit le header `Authorization: Bearer <token>`,
décode le JWT, charge l'utilisateur en base et le renvoie.

`require_role(...)` : factory qui renvoie une dépendance vérifiant que
l'utilisateur courant possède l'un des rôles autorisés.
"""
# On importe uuid pour convertir le texte du token en vrai identifiant UUID
import uuid

# Depends : injection de dépendances / HTTPException : renvoyer une erreur HTTP / status : codes HTTP lisibles
from fastapi import Depends, HTTPException, status
# HTTPBearer lit le header Authorization ; HTTPAuthorizationCredentials représente le token reçu
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# Session : type de la connexion à la base de données (SQLAlchemy)
from sqlalchemy.orm import Session

# get_db : fonction qui fournit une session de base de données à chaque requête
from app.database import get_db
# On importe le modèle User, l'énumération des rôles et celle des statuts de compte
from app.models import User, UserRole, UserStatus
# Fonction qui décode et vérifie un token JWT
from app.security import decode_access_token

# `HTTPBearer` extrait automatiquement le token du header `Authorization: Bearer <token>`.
# `auto_error=False` : on veut gérer nous-mêmes l'absence de header (pour un message custom).
# On crée le "schéma" de sécurité qui va lire le token dans chaque requête
bearer_scheme = HTTPBearer(auto_error=False)


# Dépendance qui retourne l'utilisateur actuellement connecté
def get_current_user(
    # Le token envoyé par le client (ou None s'il est absent), fourni par bearer_scheme
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    # La session de base de données, fournie automatiquement par FastAPI
    db: Session = Depends(get_db),
# La fonction renvoie un objet User
) -> User:
    """Récupère l'utilisateur courant à partir du JWT.

    Étapes :
      1. Vérifie que le header `Authorization: Bearer <token>` est présent.
      2. Décode le JWT (signature + expiration).
      3. Charge l'utilisateur en base.
      4. Vérifie que le compte n'est pas désactivé.
    """
    # Étape 1 : header présent ?
    # Si aucun header, ou token vide, on refuse la requête
    if credentials is None or not credentials.credentials:
        # On interrompt la requête avec une erreur HTTP
        raise HTTPException(
            # Code 401 : non authentifié
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Message d'erreur renvoyé au client
            detail="Token d'authentification manquant.",
            # En-tête standard indiquant au client qu'il faut un token Bearer
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 2 : décoder le JWT
    # On décode le token ; on récupère le "sub" (l'id de l'utilisateur) ou None si invalide
    subject = decode_access_token(credentials.credentials)
    # Si le décodage a échoué (signature fausse ou token expiré)
    if subject is None:
        # On refuse avec une erreur 401
        raise HTTPException(
            # Code 401 : non authentifié
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Message d'erreur renvoyé au client
            detail="Token invalide ou expiré.",
            # En-tête standard Bearer
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 3 : charger l'utilisateur
    # On tente de convertir le texte du token en UUID
    try:
        # Conversion du "sub" (texte) en objet UUID
        user_id = uuid.UUID(subject)
    # Si le texte n'est pas un UUID valide, Python lève une ValueError
    except ValueError:
        # Token falsifié ou mal formé : on refuse
        raise HTTPException(
            # Code 401 : non authentifié
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Message d'erreur renvoyé au client
            detail="Token invalide.",
            # En-tête standard Bearer
            headers={"WWW-Authenticate": "Bearer"},
        )

    # On cherche l'utilisateur en base grâce à sa clé primaire (son UUID)
    user = db.get(User, user_id)
    # Si aucun utilisateur ne correspond (par exemple compte supprimé)
    if user is None:
        # On refuse avec une erreur 401
        raise HTTPException(
            # Code 401 : non authentifié
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Message d'erreur renvoyé au client
            detail="Utilisateur introuvable.",
            # En-tête standard Bearer
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 4 : compte actif ?
    # Si le compte a été désactivé par un administrateur
    if user.status == UserStatus.DISABLED:
        # Code 403 : l'utilisateur est identifié mais n'a pas le droit d'accéder
        raise HTTPException(
            # Code 403 : accès interdit
            status_code=status.HTTP_403_FORBIDDEN,
            # Message d'erreur renvoyé au client
            detail="Ce compte a été désactivé.",
        )

    # Toutes les vérifications sont passées : on renvoie l'utilisateur
    return user


# Factory : fonction qui fabrique une dépendance, avec une liste de rôles autorisés en paramètre
def require_role(*allowed_roles: UserRole):
    """Factory : renvoie une dépendance qui vérifie que l'utilisateur
    courant possède l'un des rôles autorisés.

    Usage :
        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_role(UserRole.SUPER_ADMIN))):
            ...
    """

    # Fonction interne (closure) : elle se souvient de allowed_roles
    # Elle dépend de get_current_user, donc l'utilisateur est déjà authentifié ici
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        # Si le rôle de l'utilisateur n'est pas dans la liste des rôles autorisés
        if current_user.role not in allowed_roles:
            # On refuse avec une erreur 403
            raise HTTPException(
                # Code 403 : accès interdit
                status_code=status.HTTP_403_FORBIDDEN,
                # Message d'erreur renvoyé au client
                detail="Accès refusé : rôle insuffisant.",
            )
        # Le rôle est bon : on renvoie l'utilisateur
        return current_user

    # On renvoie la fonction de vérification, que FastAPI utilisera avec Depends(...)
    return _checker
