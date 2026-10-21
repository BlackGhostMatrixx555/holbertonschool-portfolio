"""
Routes d'authentification.

- POST /api/auth/login    : authentifie et renvoie un JWT.
- POST /api/auth/register : inscription publique d'un nouvel organisateur.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
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


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    service: UserService = Depends(get_user_service),
):
    """Inscription publique d'un nouvel organisateur (rôle SEM par défaut).

    Cet endpoint est public (pas d'authentification requise). Il permet à
    un visiteur de créer son propre compte organisateur sans passer par
    le super admin.
    """
    # Vérifier que l'email n'est pas déjà utilisé
    if service.get_by_email(data.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    # Créer l'utilisateur avec le rôle SEM (organisateur) par défaut.
    # Le super admin ne peut pas être créé via cet endpoint public (sécurité).
    user = service.create(
        UserCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password=data.password,
            role=UserRole.SEM,
        )
    )
    return user
