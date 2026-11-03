"""
Routes pour la double authentification (2FA).
"""
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# settings : configuration de l'application (ici la durée de vie des tokens)
from app.config import settings
# get_db : fournit une session de base de données par requête
from app.database import get_db
# get_current_user : renvoie l'utilisateur connecté à partir de son JWT
from app.dependencies import get_current_user
# User : modèle utilisateur de la base
from app.models import User
# TokenResponse : schéma de la réponse contenant un JWT
from app.schemas.auth import TokenResponse
# Schémas de la 2FA : réponse du setup, code à valider, requête de login avec token temporaire
from app.schemas.two_factor import (
    TwoFactorLoginRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
)
# create_access_token : génère un JWT signé
from app.security import create_access_token
# TwoFactorService : contient la logique TOTP (génération de secret, vérification de code)
from app.services.two_factor_service import TwoFactorService

# Groupe de routes préfixé par /auth/2fa, rangé sous le tag "2fa" dans la doc Swagger
router = APIRouter(prefix="/auth/2fa", tags=["2fa"])


# Fabrique du service : FastAPI lui passe automatiquement la session de base de données
def get_2fa_service(db: Session = Depends(get_db)) -> TwoFactorService:
    # On renvoie un service branché sur cette session
    return TwoFactorService(db)


# Route POST /auth/2fa/setup : prépare l'activation de la 2FA (étape 1)
@router.post("/setup", response_model=TwoFactorSetupResponse)
def setup_2fa(
    # Service 2FA injecté automatiquement
    service: TwoFactorService = Depends(get_2fa_service),
    # Utilisateur connecté : seul un utilisateur authentifié peut activer sa 2FA
    current_user: User = Depends(get_current_user),
):
    """Génère un secret TOTP et un QR code pour activer la 2FA."""
    # Le service crée un secret, le stocke et renvoie le QR code à scanner
    return service.generate_secret(current_user)


# Route POST /auth/2fa/enable : confirme l'activation avec un premier code (étape 2)
@router.post("/enable", status_code=status.HTTP_200_OK)
def enable_2fa(
    # Corps de la requête : le code à 6 chiffres lu depuis l'application d'authentification
    data: TwoFactorVerifyRequest,
    # Service 2FA injecté automatiquement
    service: TwoFactorService = Depends(get_2fa_service),
    # Utilisateur connecté
    current_user: User = Depends(get_current_user),
):
    """Valide le premier code et active la 2FA."""
    # Le code doit être valide : cela prouve que l'utilisateur a bien scanné le QR code
    if not service.enable_2fa(current_user, data.code):
        raise HTTPException(status_code=400, detail="Code 2FA invalide.")
    return {"status": "ok", "message": "2FA activée avec succès."}


# Route POST /auth/2fa/disable : désactive la 2FA
@router.post("/disable", status_code=status.HTTP_200_OK)
def disable_2fa(
    # Service 2FA injecté automatiquement
    service: TwoFactorService = Depends(get_2fa_service),
    # Utilisateur connecté
    current_user: User = Depends(get_current_user),
):
    """Désactive la 2FA."""
    # Aucun code demandé ici : voir les points d'attention ci-dessous
    service.disable_2fa(current_user)
    return {"status": "ok", "message": "2FA désactivée."}


# Route POST /auth/2fa/login : deuxième étape de connexion pour un compte protégé par la 2FA
@router.post("/login", response_model=TokenResponse)
def login_2fa(
    # Corps : le token temporaire reçu après le mot de passe, et le code à 6 chiffres
    data: TwoFactorLoginRequest,
    # Service 2FA injecté automatiquement (pas d'utilisateur connecté ici, il n'a pas encore de JWT complet)
    service: TwoFactorService = Depends(get_2fa_service),
):
    """Valide le code 2FA et renvoie un vrai JWT."""
    # Étape 1 : on retrouve l'utilisateur à partir du token temporaire (vérifie sa signature et son expiration)
    user = service.verify_temp_token(data.temp_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Token temporaire invalide ou expiré.")

    # Étape 2 : on contrôle le code TOTP de l'application d'authentification
    if not service.verify_code(user, data.code):
        raise HTTPException(status_code=401, detail="Code 2FA invalide.")

    # Étape 3 : les deux facteurs sont validés, on délivre le vrai JWT d'accès
    token = create_access_token(subject=str(user.id))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        # Durée de validité convertie de minutes en secondes, conformément à la convention OAuth2
        expires_in=settings.access_token_expire_minutes * 60,
    )
