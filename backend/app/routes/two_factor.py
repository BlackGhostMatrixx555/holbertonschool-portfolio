"""
Routes pour la double authentification (2FA).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import TokenResponse
from app.schemas.two_factor import (
    TwoFactorLoginRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
)
from app.security import create_access_token
from app.services.two_factor_service import TwoFactorService

router = APIRouter(prefix="/auth/2fa", tags=["2fa"])


def get_2fa_service(db: Session = Depends(get_db)) -> TwoFactorService:
    return TwoFactorService(db)


@router.post("/setup", response_model=TwoFactorSetupResponse)
def setup_2fa(
    service: TwoFactorService = Depends(get_2fa_service),
    current_user: User = Depends(get_current_user),
):
    """Génère un secret TOTP et un QR code pour activer la 2FA."""
    return service.generate_secret(current_user)


@router.post("/enable", status_code=status.HTTP_200_OK)
def enable_2fa(
    data: TwoFactorVerifyRequest,
    service: TwoFactorService = Depends(get_2fa_service),
    current_user: User = Depends(get_current_user),
):
    """Valide le premier code et active la 2FA."""
    if not service.enable_2fa(current_user, data.code):
        raise HTTPException(status_code=400, detail="Code 2FA invalide.")
    return {"status": "ok", "message": "2FA activée avec succès."}


@router.post("/disable", status_code=status.HTTP_200_OK)
def disable_2fa(
    service: TwoFactorService = Depends(get_2fa_service),
    current_user: User = Depends(get_current_user),
):
    """Désactive la 2FA."""
    service.disable_2fa(current_user)
    return {"status": "ok", "message": "2FA désactivée."}


@router.post("/login", response_model=TokenResponse)
def login_2fa(
    data: TwoFactorLoginRequest,
    service: TwoFactorService = Depends(get_2fa_service),
):
    """Valide le code 2FA et renvoie un vrai JWT."""
    user = service.verify_temp_token(data.temp_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Token temporaire invalide ou expiré.")

    if not service.verify_code(user, data.code):
        raise HTTPException(status_code=401, detail="Code 2FA invalide.")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )
