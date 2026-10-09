"""
Dépendances FastAPI partagées.

`get_current_user` : lit le header `Authorization: Bearer <token>`,
décode le JWT, charge l'utilisateur en base et le renvoie.

`require_role(...)` : factory qui renvoie une dépendance vérifiant que
l'utilisateur courant possède l'un des rôles autorisés.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, UserStatus
from app.security import decode_access_token

# `HTTPBearer` extrait automatiquement le token du header `Authorization: Bearer <token>`.
# `auto_error=False` : on veut gérer nous-mêmes l'absence de header (pour un message custom).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Récupère l'utilisateur courant à partir du JWT.

    Étapes :
      1. Vérifie que le header `Authorization: Bearer <token>` est présent.
      2. Décode le JWT (signature + expiration).
      3. Charge l'utilisateur en base.
      4. Vérifie que le compte n'est pas désactivé.
    """
    # Étape 1 : header présent ?
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 2 : décoder le JWT
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 3 : charger l'utilisateur
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Étape 4 : compte actif ?
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été désactivé.",
        )

    return user


def require_role(*allowed_roles: UserRole):
    """Factory : renvoie une dépendance qui vérifie que l'utilisateur
    courant possède l'un des rôles autorisés.

    Usage :
        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_role(UserRole.SUPER_ADMIN))):
            ...
    """

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé : rôle insuffisant.",
            )
        return current_user

    return _checker
