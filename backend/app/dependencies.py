"""
Dépendances FastAPI partagées.

Pour l'instant : un stub de `get_current_user` qui lit l'utilisateur depuis
le header `X-User-Id`. Ça permet de développer les endpoints CRUD (étape 4)
sans attendre l'authentification JWT (étape 5).

⚠️ À remplacer à l'étape 5 par une vraie vérification de token JWT.
"""
import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(
    x_user_id: uuid.UUID | None = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    """Récupère l'utilisateur courant à partir du header `X-User-Id`.

    Stub temporaire : aucune vérification de token. Sert uniquement à
    développer les endpoints en attendant l'étape 5.
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-User-Id manquant.",
        )

    user = db.get(User, x_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )
    return user
