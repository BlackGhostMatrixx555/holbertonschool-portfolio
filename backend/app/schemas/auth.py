"""
Schémas Pydantic pour l'authentification.
"""
from pydantic import BaseModel, Field

from app.schemas.types import DevEmailStr as EmailStr


class LoginRequest(BaseModel):
    """Données envoyées par le client pour se connecter."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Données pour l'inscription publique d'un nouvel organisateur."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Réponse renvoyée après un login réussi (avec ou sans 2FA).
    
    - Si `requires_2fa` est True, `temp_token` contient un JWT temporaire.
    - Sinon, `access_token` contient le vrai JWT.
    """
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 0
    requires_2fa: bool = False
    temp_token: str | None = None
