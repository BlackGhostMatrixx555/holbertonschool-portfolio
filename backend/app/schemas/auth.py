"""
Schémas Pydantic pour l'authentification.
"""
# BaseModel : classe de base des schémas Pydantic
# Field : permet d'ajouter des contraintes de validation sur un champ (longueur min/max, etc.)
from pydantic import BaseModel, Field

# DevEmailStr (renommé EmailStr) : type d'email personnalisé du projet, utilisé partout pour rester cohérent
from app.schemas.types import DevEmailStr as EmailStr


# Schéma ENTRANT : ce que le client envoie pour se connecter
class LoginRequest(BaseModel):
    """Données envoyées par le client pour se connecter."""
    # Email du compte : validé au format email
    email: EmailStr
    # Mot de passe en clair (envoyé via HTTPS) : obligatoire, au moins 1 caractère
    # (pas de contrainte de longueur minimale de 8 ici : on vérifie seulement qu'il n'est pas vide, la vraie vérification se fait contre le hash en base)
    password: str = Field(..., min_length=1)


# Schéma ENTRANT : ce que le client envoie pour créer un compte organisateur (inscription publique)
class RegisterRequest(BaseModel):
    """Données pour l'inscription publique d'un nouvel organisateur."""
    # Prénom : obligatoire (...), entre 1 et 100 caractères
    first_name: str = Field(..., min_length=1, max_length=100)
    # Nom de famille : obligatoire, entre 1 et 100 caractères
    last_name: str = Field(..., min_length=1, max_length=100)
    # Email : validé au format email, servira d'identifiant de connexion
    email: EmailStr
    # Mot de passe : entre 8 et 128 caractères (minimum de sécurité, maximum pour éviter les abus lors du hachage bcrypt)
    password: str = Field(..., min_length=8, max_length=128)


# Schéma SORTANT : ce que l'API renvoie après une tentative de connexion réussie
class TokenResponse(BaseModel):
    """Réponse renvoyée après un login réussi (avec ou sans 2FA).
    
    - Si `requires_2fa` est True, `temp_token` contient un JWT temporaire.
    - Sinon, `access_token` contient le vrai JWT.
    """
    # Vrai JWT d'accès : None tant que la 2FA n'a pas été validée (si elle est activée)
    access_token: str | None = None
    # Type de token : "bearer" correspond au header "Authorization: Bearer <token>"
    token_type: str = "bearer"
    # Durée de validité du token en secondes : 0 si aucun access_token n'est délivré
    expires_in: int = 0
    # Indique au frontend si une deuxième étape (code 2FA) est nécessaire
    requires_2fa: bool = False
    # Token temporaire à renvoyer avec le code 2FA (voir TwoFactorLoginRequest) : None si la 2FA n'est pas requise
    temp_token: str | None = None
