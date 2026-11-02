"""Schémas de l'authentification."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # L'email reste un simple str ici : un email mal formé doit recevoir la
    # même réponse 401 qu'un mauvais mot de passe (pas d'indice pour un attaquant).
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
