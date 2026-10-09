"""
Schémas Pydantic pour l'authentification.
"""
from pydantic import BaseModel, Field

from app.schemas.types import DevEmailStr as EmailStr


class LoginRequest(BaseModel):
    """Données envoyées par le client pour se connecter."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Réponse renvoyée après un login réussi."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # secondes
