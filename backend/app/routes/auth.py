"""
Routes d'authentification.

- POST /api/auth/login : authentifie et renvoie un JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    """Authentifie un utilisateur et renvoie un token JWT.

    Le client devra ensuite envoyer ce token dans le header
    `Authorization: Bearer <token>` pour les requêtes protégées.
    """
    user = service.authenticate(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )
