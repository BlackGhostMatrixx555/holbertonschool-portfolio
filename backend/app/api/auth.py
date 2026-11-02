"""Routes d'authentification : connexion et profil connecté."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserView
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Échange email + mot de passe contre un jeton JWT."""
    try:
        return user_service.authenticate(db, payload.email, payload.password)
    except user_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me", response_model=UserView)
def read_me(current_user: User = Depends(get_current_user)):
    """Profil de l'utilisateur connecté (utilisé par le front-end au chargement)."""
    return current_user
