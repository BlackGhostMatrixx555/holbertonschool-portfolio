"""
Routes d'authentification : connexion (1 ou 2 étapes), inscription, profil,
double authentification et vérification email / SMS.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.mongo import get_mongo_db
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    TwoFactorCode,
    TwoFactorLoginRequest,
    TwoFactorSetupResponse,
    VerificationCheck,
    VerificationSent,
)
from app.schemas.user import UserView
from app.services import two_factor_service, user_service, verification_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Étape 1 : email + mot de passe. Renvoie un jeton, ou un jeton temporaire si la 2FA est active."""
    try:
        return user_service.authenticate(db, payload.email, payload.password)
    except user_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except user_service.PendingAccountError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/register", response_model=UserView, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Inscription publique d'un organisateur ; le compte doit être activé par le super admin."""
    return user_service.register(db, payload)


@router.get("/me", response_model=UserView)
def read_me(current_user: User = Depends(get_current_user)):
    """Profil de l'utilisateur connecté (utilisé par le front-end au chargement)."""
    return current_user


# ---- Double authentification ----------------------------------------------------

@router.post("/2fa/login", response_model=TokenResponse)
def login_two_factor(payload: TwoFactorLoginRequest, db: Session = Depends(get_db)):
    """Étape 2 : jeton temporaire + code à 6 chiffres -> jeton de session."""
    try:
        user = two_factor_service.verify_login(db, payload.temp_token, payload.code)
    except two_factor_service.InvalidTwoFactorError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return user_service.complete_two_factor_login(user)


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return two_factor_service.setup(db, current_user)


@router.post("/2fa/enable", response_model=MessageResponse)
def enable_two_factor(payload: TwoFactorCode, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    two_factor_service.enable(db, current_user, payload.code)
    return {"message": "Double authentification activée."}


@router.post("/2fa/disable", response_model=MessageResponse)
def disable_two_factor(payload: TwoFactorCode, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    two_factor_service.disable(db, current_user, payload.code)
    return {"message": "Double authentification désactivée."}


# ---- Vérification email / SMS ------------------------------------------------

@router.post("/verify/send-email", response_model=VerificationSent)
def send_email_code(current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):
    return verification_service.send_code(mongo, current_user, "email")


@router.post("/verify/send-sms", response_model=VerificationSent)
def send_sms_code(current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):
    return verification_service.send_code(mongo, current_user, "sms")


@router.post("/verify/check-code", response_model=MessageResponse)
def check_code(payload: VerificationCheck, current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):
    verification_service.check_code(mongo, current_user, payload.code)
    return {"message": "Code validé."}
