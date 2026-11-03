"""
Routes pour la vérification par SMS et Email.
"""
# APIRouter : permet de regrouper des routes dans un module séparé
# Depends : injection de dépendances FastAPI (la base, le service, l'utilisateur connecté)
# HTTPException : permet de renvoyer une erreur HTTP avec un code et un message
from fastapi import APIRouter, Depends, HTTPException
# BaseModel : classe de base des schémas Pydantic
from pydantic import BaseModel
# Session : type de la session SQLAlchemy (une session = une transaction avec la base)
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données à chaque requête
from app.database import get_db
# get_current_user : vérifie le JWT et renvoie l'utilisateur connecté
from app.dependencies import get_current_user
# User : modèle utilisateur de la base
from app.models import User
# VerificationService : contient la logique de génération et de contrôle des codes
from app.services.verification_service import VerificationService

# Crée un groupe de routes : toutes commencent par /auth/verify et sont rangées sous le tag "verification" dans la doc
router = APIRouter(prefix="/auth/verify", tags=["verification"])


# Fabrique du service : FastAPI l'appelle automatiquement en lui passant la session de base de données
def get_verification_service(db: Session = Depends(get_db)) -> VerificationService:
    # On crée et on renvoie un service de vérification branché sur cette session
    return VerificationService(db)


# Schéma ENTRANT : le code reçu par l'utilisateur, à vérifier
class VerifyCodeRequest(BaseModel):
    # Code de vérification saisi par l'utilisateur (aucune contrainte de longueur ici)
    code: str


# Route POST /auth/verify/send-sms : demande l'envoi d'un code par SMS
@router.post("/send-sms")
def send_sms(
    # Service de vérification injecté automatiquement
    service: VerificationService = Depends(get_verification_service),
    # Utilisateur connecté : la route n'est accessible qu'avec un JWT valide
    current_user: User = Depends(get_current_user),
):
    """Envoie un code de vérification par SMS (Mock)."""
    # On tente d'envoyer le code ; le service génère un code et le stocke pour cet utilisateur
    try:
        code = service.send_sms_code(current_user)
        # `debug_code` est exposé uniquement pour faciliter les tests.
        # En production, on ne le renvoie JAMAIS.
        return {"status": "ok", "message": "Code SMS envoyé.", "debug_code": code}
    # Si le service lève une ValueError (ex. pas de numéro de téléphone renseigné), on renvoie une erreur 400
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Route POST /auth/verify/send-email : demande l'envoi d'un code par email
@router.post("/send-email")
def send_email(
    # Service de vérification injecté automatiquement
    service: VerificationService = Depends(get_verification_service),
    # Utilisateur connecté : accès réservé aux comptes authentifiés
    current_user: User = Depends(get_current_user),
):
    """Envoie un code de vérification par Email (Mock)."""
    # Génère le code et le rattache à l'utilisateur courant
    code = service.send_email_code(current_user)
    # Renvoie le code en clair pour les tests (voir remarque sur debug_code plus haut)
    return {"status": "ok", "message": "Code Email envoyé.", "debug_code": code}


# Route POST /auth/verify/check-code : contrôle le code saisi par l'utilisateur
@router.post("/check-code")
def check_code(
    # Corps de la requête : le code à vérifier, validé par VerifyCodeRequest
    data: VerifyCodeRequest,
    # Service de vérification injecté automatiquement
    service: VerificationService = Depends(get_verification_service),
    # Utilisateur connecté : on ne peut valider que son propre code
    current_user: User = Depends(get_current_user),
):
    """Vérifie un code reçu par SMS ou Email."""
    # Si le code correspond et n'a pas expiré, on confirme la validation
    if service.verify_code(current_user, data.code):
        return {"status": "ok", "message": "Code validé."}
    # Sinon, erreur 400 : le code est faux ou périmé (message volontairement identique dans les deux cas)
    raise HTTPException(status_code=400, detail="Code invalide ou expiré.")
