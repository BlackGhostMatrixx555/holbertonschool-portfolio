"""
Schémas Pydantic pour la double authentification (2FA).
"""
# BaseModel : classe de base des schémas Pydantic
# Field : permet d'ajouter des contraintes de validation sur un champ (longueur min/max, etc.)
from pydantic import BaseModel, Field


# Schéma des données SORTANTES : ce que l'API renvoie quand l'utilisateur active la 2FA
class TwoFactorSetupResponse(BaseModel):
    """Réponse envoyée lors de l'initialisation de la 2FA."""
    # Clé secrète TOTP : l'utilisateur peut la saisir à la main dans son application d'authentification
    secret: str
    # URL au format otpauth:// : contient le secret et les infos du compte, c'est ce que lit l'application
    otpauth_url: str
    # Image du QR code encodée en base64 : le frontend l'affiche pour que l'utilisateur la scanne avec son téléphone
    qr_code_base64: str


# Schéma des données ENTRANTES : ce que le client envoie pour valider un code 2FA
class TwoFactorVerifyRequest(BaseModel):
    """Code à 6 chiffres envoyé par l'utilisateur."""
    # Code temporaire affiché par l'application d'authentification : obligatoire (...), exactement 6 caractères
    code: str = Field(..., min_length=6, max_length=6)


# Schéma des données ENTRANTES : ce que le client envoie pour finaliser une connexion protégée par la 2FA
class TwoFactorLoginRequest(BaseModel):
    """Code à 6 chiffres envoyé lors du login 2FA."""
    # Token temporaire reçu après la première étape de connexion (email + mot de passe corrects)
    temp_token: str
    # Code à 6 chiffres de l'application d'authentification : obligatoire, exactement 6 caractères
    code: str = Field(..., min_length=6, max_length=6)
