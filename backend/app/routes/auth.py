"""
Routes d'authentification.

- POST /api/auth/login    : authentifie (retourne un JWT ou un temp_token pour 2FA).
- POST /api/auth/register : inscription publique d'un nouvel organisateur.
- GET  /api/auth/me       : profil de l'utilisateur connecté.
"""
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# settings : configuration de l'application (durée de vie du token, etc.)
from app.config import settings
# get_db : fournit une session de base de données par requête
from app.database import get_db
# get_current_user : renvoie l'utilisateur connecté à partir de son JWT
from app.dependencies import get_current_user
# User et UserRole : modèle utilisateur et énumération des rôles
from app.models import User, UserRole
# Schémas de validation : connexion, inscription et réponse contenant le token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
# Schémas utilisateur : création interne et lecture publique
from app.schemas.user import UserCreate, UserRead
# create_access_token : fabrique un JWT signé pour un utilisateur
from app.security import create_access_token
# Services métier : gestion de la 2FA et des utilisateurs
from app.services.two_factor_service import TwoFactorService
from app.services.user_service import UserService

# Groupe de routes préfixé par /auth, rangé sous le tag "auth" dans la doc Swagger
router = APIRouter(prefix="/auth", tags=["auth"])


# Fabrique du service utilisateurs : FastAPI lui passe la session de base de données
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    # On renvoie un service branché sur cette session
    return UserService(db)


# Fabrique du service 2FA : même principe
def get_2fa_service(db: Session = Depends(get_db)) -> TwoFactorService:
    # On renvoie un service branché sur cette session
    return TwoFactorService(db)


# Route POST /auth/login : vérifie les identifiants et renvoie un token
@router.post("/login", response_model=TokenResponse)
def login(
    # Corps de la requête : email et mot de passe, validés automatiquement
    data: LoginRequest,
    # Services injectés automatiquement
    service: UserService = Depends(get_user_service),
    twofa_service: TwoFactorService = Depends(get_2fa_service),
):
    """Authentifie un utilisateur. Si la 2FA est activée, renvoie un temp_token."""
    # On vérifie l'email et le mot de passe, le service renvoie None en cas d'échec
    user = service.authenticate(data.email, data.password)
    # Identifiants incorrects : erreur 401
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    # Si la 2FA est activée, on ne délivre pas encore le vrai token
    if user.is_2fa_enabled:
        # On crée un token temporaire, valable seulement pour l'étape du code 2FA
        temp_token = twofa_service.create_temp_token(user)
        # Réponse indiquant au frontend qu'il faut demander le code 2FA
        return TokenResponse(
            requires_2fa=True,
            temp_token=temp_token,
        )

    # Sinon, connexion classique : on crée le JWT, l'identifiant de l'utilisateur est le sujet
    token = create_access_token(subject=str(user.id))
    # On renvoie le token, son type et sa durée de validité en secondes
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# Route POST /auth/register : inscription publique (201 à la création)
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    # Corps de la requête : prénom, nom, email et mot de passe
    data: RegisterRequest,
    service: UserService = Depends(get_user_service),
):
    """Inscription publique d'un nouvel organisateur (rôle SEM par défaut)."""
    # On vérifie qu'aucun compte n'utilise déjà cet email
    if service.get_by_email(data.email) is not None:
        # Email déjà pris : erreur 409 (conflit)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    # Création du compte, avec le rôle SEM imposé : l'utilisateur ne peut pas choisir son rôle
    user = service.create(
        UserCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password=data.password,
            role=UserRole.SEM,
        )
    )
    # Le compte créé est renvoyé, sans le mot de passe grâce au schéma UserRead
    return user


# ---------------------------------------------------------------------------
# NOUVEAU : Profil de l'utilisateur connecté
# ---------------------------------------------------------------------------
# Route GET /auth/me : renvoie le profil de l'utilisateur dont le JWT est valide
@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté (via JWT)."""
    # get_current_user a déjà fait toute la vérification, on renvoie simplement l'utilisateur
    return current_user
