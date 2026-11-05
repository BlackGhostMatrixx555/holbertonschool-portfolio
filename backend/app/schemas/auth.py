"""Schémas de l'authentification : connexion, inscription, 2FA, vérification."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    # L'email reste un simple str ici : un email mal formé doit recevoir la
    # même réponse 401 qu'un mauvais mot de passe (pas d'indice pour un attaquant).
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    """
    Réponse de connexion, en une ou deux étapes :
    - sans 2FA : access_token est rempli ;
    - avec 2FA : requires_2fa = True et temp_token sert à l'étape 2.
    """

    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 0
    requires_2fa: bool = False
    temp_token: str | None = None


class RegisterRequest(BaseModel):
    """Inscription publique d'un organisateur (compte à valider par le super admin)."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    # 12 caractères minimum : recommandation de l'ANSSI pour un mot de passe seul.
    password: str = Field(min_length=12, max_length=128)
    phone_number: str | None = Field(default=None, pattern=r"^\+?[0-9 .-]{6,20}$")


# ---- Double authentification (TOTP) -------------------------------------------

class TwoFactorSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TwoFactorCode(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class TwoFactorLoginRequest(BaseModel):
    temp_token: str
    code: str = Field(pattern=r"^\d{6}$")


# ---- Vérification par email / SMS -------------------------------------------

class VerificationSent(BaseModel):
    message: str
    # Renvoyé uniquement en développement (envoi simulé), jamais en production.
    debug_code: str | None = None


class VerificationCheck(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class MessageResponse(BaseModel):
    message: str
