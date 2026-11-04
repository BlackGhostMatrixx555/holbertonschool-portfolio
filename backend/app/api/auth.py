"""
Routes d'authentification : connexion (1 ou 2 étapes), inscription, profil,
double authentification et vérification email / SMS.
"""  # Docstring du module : résume les quatre familles de routes du fichier.
from fastapi import APIRouter, Depends, HTTPException, status  # APIRouter pour grouper les routes, Depends pour l'injection, HTTPException pour renvoyer des erreurs, status pour les codes HTTP nommés.
from pymongo.database import Database  # Type d'une base MongoDB, utilisée ici pour la vérification email/SMS.
from sqlalchemy.orm import Session  # Type d'une session de base de données relationnelle.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.mongo import get_mongo_db  # Fournit une connexion à MongoDB.
from app.db.session import get_db  # Fournit une session de base de données relationnelle.
from app.models import User  # Modèle utilisateur.
from app.schemas.auth import (  # Schémas d'entrée et de sortie des routes d'authentification.
    LoginRequest,  # Email et mot de passe pour la connexion.
    MessageResponse,  # Réponse simple contenant un message.
    RegisterRequest,  # Données d'inscription.
    TokenResponse,  # Jeton d'accès renvoyé après connexion.
    TwoFactorCode,  # Code à 6 chiffres pour activer ou désactiver la 2FA.
    TwoFactorLoginRequest,  # Jeton temporaire et code pour l'étape 2 de connexion.
    TwoFactorSetupResponse,  # Données renvoyées lors de la configuration de la 2FA.
    VerificationCheck,  # Code de vérification saisi par l'utilisateur.
    VerificationSent,  # Confirmation d'envoi d'un code de vérification.
)
from app.schemas.user import UserView  # Schéma de sortie décrivant un utilisateur.
from app.services import two_factor_service, user_service, verification_service  # Couches service : 2FA, gestion des utilisateurs et vérification.

router = APIRouter(prefix="/auth", tags=["Authentification"])  # Routeur préfixé par /auth, regroupé sous "Authentification" dans Swagger.

@router.post("/login", response_model=TokenResponse)  # Route POST /auth/login : étape 1 de connexion.
def login(payload: LoginRequest, db: Session = Depends(get_db)):  # Reçoit email et mot de passe, injecte la session.
    """Étape 1 : email + mot de passe. Renvoie un jeton, ou un jeton temporaire si la 2FA est active."""  # Docstring visible dans Swagger.
    try:  # Tente l'authentification.
        return user_service.authenticate(db, payload.email, payload.password)  # Renvoie le jeton, ou le jeton temporaire si la 2FA est activée.
    except user_service.InvalidCredentialsError as exc:  # Identifiants incorrects.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))  # Renvoie une erreur 401 avec le message du service.
    except user_service.PendingAccountError as exc:  # Compte existant mais non encore activé.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))  # Renvoie une erreur 403 avec le message du service.

@router.post("/register", response_model=UserView, status_code=status.HTTP_201_CREATED)  # Route POST /auth/register : inscription, réponse 201.
def register(payload: RegisterRequest, db: Session = Depends(get_db)):  # Reçoit les données d'inscription et la session.
    """Inscription publique d'un organisateur ; le compte doit être activé par le super admin."""  # Docstring visible dans Swagger.
    return user_service.register(db, payload)  # Délègue la création du compte au service, qui renvoie l'utilisateur créé en attente d'activation.

@router.get("/me", response_model=UserView)  # Route GET /auth/me : profil de l'utilisateur connecté.
def read_me(current_user: User = Depends(get_current_user)):  # L'utilisateur est fourni par la dépendance d'authentification.
    """Profil de l'utilisateur connecté (utilisé par le front-end au chargement)."""  # Docstring visible dans Swagger.
    return current_user  # Renvoie directement l'utilisateur, sérialisé selon UserView.

# ---- Double authentification ----------------------------------------------------

@router.post("/2fa/login", response_model=TokenResponse)  # Route POST /auth/2fa/login : étape 2 de connexion.
def login_two_factor(payload: TwoFactorLoginRequest, db: Session = Depends(get_db)):  # Reçoit le jeton temporaire et le code, injecte la session.
    """Étape 2 : jeton temporaire + code à 6 chiffres -> jeton de session."""  # Docstring visible dans Swagger.
    try:  # Tente la vérification du code.
        user = two_factor_service.verify_login(db, payload.temp_token, payload.code)  # Vérifie le jeton temporaire et le code, et renvoie l'utilisateur correspondant.
    except two_factor_service.InvalidTwoFactorError as exc:  # Code ou jeton invalide.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))  # Renvoie une erreur 401.
    return user_service.complete_two_factor_login(user)  # Une fois le code validé, émet le jeton de session définitif.

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)  # Route POST /auth/2fa/setup : début de la configuration de la 2FA.
def setup_two_factor(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Utilisateur connecté et session.
    return two_factor_service.setup(db, current_user)  # Délègue au service, qui génère le secret et les informations à faire scanner à l'utilisateur.

@router.post("/2fa/enable", response_model=MessageResponse)  # Route POST /auth/2fa/enable : activation de la 2FA après vérification d'un code.
def enable_two_factor(payload: TwoFactorCode, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Code reçu, utilisateur connecté et session.
    two_factor_service.enable(db, current_user, payload.code)  # Vérifie le code puis active la 2FA ; lève une erreur en cas d'échec.
    return {"message": "Double authentification activée."}  # Message de confirmation.

@router.post("/2fa/disable", response_model=MessageResponse)  # Route POST /auth/2fa/disable : désactivation de la 2FA après vérification d'un code.
def disable_two_factor(payload: TwoFactorCode, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Code reçu, utilisateur connecté et session.
    two_factor_service.disable(db, current_user, payload.code)  # Vérifie le code puis désactive la 2FA ; lève une erreur en cas d'échec.
    return {"message": "Double authentification désactivée."}  # Message de confirmation.

# ---- Vérification email / SMS ------------------------------------------------

@router.post("/verify/send-email", response_model=VerificationSent)  # Route POST : envoi d'un code de vérification par email.
def send_email_code(current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):  # Utilisateur connecté et connexion MongoDB, où le code est stocké.
    return verification_service.send_code(mongo, current_user, "email")  # Génère et envoie le code par email via le service.

@router.post("/verify/send-sms", response_model=VerificationSent)  # Route POST : envoi d'un code de vérification par SMS.
def send_sms_code(current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):  # Utilisateur connecté et connexion MongoDB.
    return verification_service.send_code(mongo, current_user, "sms")  # Génère et envoie le code par SMS via le service.

@router.post("/verify/check-code", response_model=MessageResponse)  # Route POST : contrôle du code saisi par l'utilisateur.
def check_code(payload: VerificationCheck, current_user: User = Depends(get_current_user), mongo: Database = Depends(get_mongo_db)):  # Code saisi, utilisateur connecté et connexion MongoDB.
    verification_service.check_code(mongo, current_user, payload.code)  # Vérifie le code auprès du service ; lève une erreur s'il est incorrect ou expiré.
    return {"message": "Code validé."}  # Message de confirmation.