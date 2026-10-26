"""
Routes pour la vérification par SMS et Email.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/auth/verify", tags=["verification"])


def get_verification_service(db: Session = Depends(get_db)) -> VerificationService:
    return VerificationService(db)


class VerifyCodeRequest(BaseModel):
    code: str


@router.post("/send-sms")
def send_sms(
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user),
):
    """Envoie un code de vérification par SMS (Mock)."""
    try:
        code = service.send_sms_code(current_user)
        # `debug_code` est exposé uniquement pour faciliter les tests.
        # En production, on ne le renvoie JAMAIS.
        return {"status": "ok", "message": "Code SMS envoyé.", "debug_code": code}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-email")
def send_email(
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user),
):
    """Envoie un code de vérification par Email (Mock)."""
    code = service.send_email_code(current_user)
    return {"status": "ok", "message": "Code Email envoyé.", "debug_code": code}


@router.post("/check-code")
def check_code(
    data: VerifyCodeRequest,
    service: VerificationService = Depends(get_verification_service),
    current_user: User = Depends(get_current_user),
):
    """Vérifie un code reçu par SMS ou Email."""
    if service.verify_code(current_user, data.code):
        return {"status": "ok", "message": "Code validé."}
    raise HTTPException(status_code=400, detail="Code invalide ou expiré.")
