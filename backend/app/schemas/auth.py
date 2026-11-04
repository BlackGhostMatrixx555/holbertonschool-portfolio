"""Schémas de l'authentification : connexion, inscription, 2FA, vérification."""  # Docstring du module : couvre la connexion, l'inscription, la double authentification et la vérification.
from pydantic import BaseModel, EmailStr, Field  # Classe de base Pydantic, validation d'email et contraintes de champs.

class LoginRequest(BaseModel):  # Identifiants envoyés par le client pour se connecter.
    # L'email reste un simple str ici : un email mal formé doit recevoir la  # Explication du choix du type str.
    # même réponse 401 qu'un mauvais mot de passe (pas d'indice pour un attaquant).  # Raison : éviter la divulgation d'information.
    email: str = Field(max_length=254)  # Email en texte libre, borné à 254 caractères (limite usuelle d'une adresse).
    password: str = Field(max_length=128)  # Mot de passe, borné à 128 caractères.

class TokenResponse(BaseModel):  # Réponse renvoyée après une tentative de connexion.
    """
    Réponse de connexion, en une ou deux étapes :
    - sans 2FA : access_token est rempli ;
    - avec 2FA : requires_2fa = True et temp_token sert à l'étape 2.
    """  # Explication des deux cas possibles selon l'activation de la 2FA.

    access_token: str | None = None  # Jeton d'accès, présent uniquement si la connexion est complète.
    token_type: str = "bearer"  # Type du jeton, bearer par défaut (norme OAuth 2).
    expires_in: int = 0  # Durée de validité du jeton d'accès, en secondes.
    requires_2fa: bool = False  # Indique qu'une étape de double authentification est nécessaire.
    temp_token: str | None = None  # Jeton temporaire transmis pour l'étape 2 de la 2FA.

class RegisterRequest(BaseModel):  # Données d'inscription publique d'un organisateur.
    """Inscription publique d'un organisateur (compte à valider par le super admin)."""  # Le compte n'est actif qu'après validation par un super admin.

    first_name: str = Field(min_length=1, max_length=100)  # Prénom, entre 1 et 100 caractères.
    last_name: str = Field(min_length=1, max_length=100)  # Nom, entre 1 et 100 caractères.
    email: EmailStr  # Adresse email validée au format.
    # 12 caractères minimum : recommandation de l'ANSSI pour un mot de passe seul.  # Justification de la longueur minimale.
    password: str = Field(min_length=12, max_length=128)  # Mot de passe entre 12 et 128 caractères.
    phone_number: str | None = Field(default=None, pattern=r"^\+?[0-9 .-]{6,20}$")  # Téléphone optionnel : chiffres, espaces, points ou tirets, avec un + facultatif.

# ---- Double authentification (TOTP) -------------------------------------------  # Séparateur de section.

class TwoFactorSetupResponse(BaseModel):  # Données renvoyées lors de l'activation de la 2FA.
    secret: str  # Secret partagé à saisir manuellement dans l'application d'authentification.
    otpauth_url: str  # URL otpauth:// permettant d'ajouter le compte à l'application.
    qr_code_base64: str  # QR code encodé en base64 pour un scan direct.

class TwoFactorCode(BaseModel):  # Code TOTP à six chiffres.
    code: str = Field(pattern=r"^\d{6}$")  # Exactement six chiffres.

class TwoFactorLoginRequest(BaseModel):  # Requête de la seconde étape de connexion avec la 2FA.
    temp_token: str  # Jeton temporaire reçu à la première étape.
    code: str = Field(pattern=r"^\d{6}$")  # Code TOTP à six chiffres.

# ---- Vérification par email / SMS -------------------------------------------  # Séparateur de section.

class VerificationSent(BaseModel):  # Confirmation d'envoi d'un code de vérification.
    message: str  # Message informatif destiné à l'utilisateur.
    # Renvoyé uniquement en développement (envoi simulé), jamais en production.  # Le code n'est jamais exposé en production.
    debug_code: str | None = None  # Code de vérification en clair, réservé au développement.

class VerificationCheck(BaseModel):  # Code saisi par l'utilisateur pour vérification.
    code: str = Field(pattern=r"^\d{6}$")  # Exactement six chiffres.

class MessageResponse(BaseModel):  # Réponse générique ne contenant qu'un message.
    message: str  # Texte du message à afficher.