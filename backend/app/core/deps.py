"""
Dépendances FastAPI partagées par toutes les routes.

FastAPI les exécute avant la route (injection de dépendances) :
une route qui déclare `current_user: User = Depends(get_current_user)`
ne s'exécute que si le jeton JWT est valide.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import ACCESS_SCOPE, decode_token
from app.db.session import get_db
from app.models import User, UserRole, UserStatus

# auto_error=False : on gère nous-mêmes l'absence de jeton pour renvoyer
# un message en français et un code 401 cohérent.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Décode le jeton "Bearer" et retourne l'utilisateur actif correspondant."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant.",
        )

    # decode_token refuse aussi les jetons temporaires 2FA (portée différente).
    subject = decode_token(credentials.credentials, ACCESS_SCOPE)
    try:
        user_id = UUID(subject or "")
    except ValueError:
        # Signature fausse, jeton expiré, mauvaise portée ou "sub" absent :
        # même réponse, pour ne rien révéler à un attaquant.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )

    user = db.get(User, user_id)
    # Un compte désactivé perd l'accès immédiatement, même avec un jeton valide.
    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )
    return user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Autorise uniquement le super admin (gestion des comptes, sauvegardes)."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes.",
        )
    return current_user
