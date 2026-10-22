"""
Schémas Pydantic pour la double authentification (2FA).
"""
from pydantic import BaseModel, Field


class TwoFactorSetupResponse(BaseModel):
    """Réponse envoyée lors de l'initialisation de la 2FA."""
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TwoFactorVerifyRequest(BaseModel):
    """Code à 6 chiffres envoyé par l'utilisateur."""
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorLoginRequest(BaseModel):
    """Code à 6 chiffres envoyé lors du login 2FA."""
    temp_token: str
    code: str = Field(..., min_length=6, max_length=6)
