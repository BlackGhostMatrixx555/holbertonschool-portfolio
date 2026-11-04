"""
Dépendances FastAPI partagées par toutes les routes.

FastAPI les exécute avant la route (injection de dépendances) :
une route qui déclare `current_user: User = Depends(get_current_user)`
ne s'exécute que si le jeton JWT est valide.
"""  # Docstring du module : principe de l'injection de dépendances.
from uuid import UUID  # Type représentant un identifiant unique, utilisé pour convertir l'identifiant du jeton.

from fastapi import Depends, HTTPException, status  # Depends pour l'injection, HTTPException pour les erreurs HTTP, status pour les codes HTTP nommés.
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # Outils de lecture de l'en-tête "Authorization: Bearer".
from sqlalchemy.orm import Session  # Type d'une session de base de données SQLAlchemy.

from app.core.security import ACCESS_SCOPE, decode_token  # Constante de portée "access" et fonction de décodage des jetons.
from app.db.session import get_db  # Dépendance fournissant une session de base de données.
from app.models import User, UserRole, UserStatus  # Modèle utilisateur, rôles et statuts possibles.

# auto_error=False : on gère nous-mêmes l'absence de jeton pour renvoyer
# un message en français et un code 401 cohérent.
bearer_scheme = HTTPBearer(auto_error=False)  # Lecteur de l'en-tête Bearer ; ne lève pas d'erreur automatique si l'en-tête est absent.

def get_current_user(  # Dépendance qui identifie l'utilisateur connecté.
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # Récupère le jeton Bearer, ou None s'il est absent.
    db: Session = Depends(get_db),  # Fournit la session de base de données.
) -> User:  # Retourne l'utilisateur authentifié.
    """Décode le jeton "Bearer" et retourne l'utilisateur actif correspondant."""  # Docstring : rôle de la fonction.
    if credentials is None:  # Aucun en-tête d'autorisation fourni.
        raise HTTPException(  # Interrompt la requête avec une erreur HTTP.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Code 401 : authentification requise.
            detail="Token d'authentification manquant.",  # Message renvoyé au client.
        )

    # decode_token refuse aussi les jetons temporaires 2FA (portée différente).
    subject = decode_token(credentials.credentials, ACCESS_SCOPE)  # Vérifie signature, expiration et portée ; retourne le sujet ou None.
    try:  # Tente de convertir le sujet en identifiant UUID.
        user_id = UUID(subject or "")  # Si subject est None, on convertit une chaîne vide, ce qui lève ValueError.
    except ValueError:  # Conversion impossible.
        # Signature fausse, jeton expiré, mauvaise portée ou "sub" absent :
        # même réponse, pour ne rien révéler à un attaquant.
        raise HTTPException(  # Interrompt la requête.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Code 401.
            detail="Token invalide ou expiré.",  # Message générique, volontairement sans détail.
        )

    user = db.get(User, user_id)  # Charge l'utilisateur correspondant à cet identifiant en base (None s'il n'existe pas).
    # Un compte désactivé perd l'accès immédiatement, même avec un jeton valide.
    if user is None or user.status != UserStatus.ACTIVE:  # Utilisateur inexistant ou compte non actif.
        raise HTTPException(  # Interrompt la requête.
            status_code=status.HTTP_401_UNAUTHORIZED,  # Code 401.
            detail="Utilisateur introuvable.",  # Message renvoyé au client.
        )
    return user  # Retourne l'utilisateur authentifié à la route appelante.

def require_super_admin(current_user: User = Depends(get_current_user)) -> User:  # Dépendance qui restreint l'accès au super admin.
    """Autorise uniquement le super admin (gestion des comptes, sauvegardes)."""  # Docstring : périmètre de la restriction.
    if current_user.role != UserRole.SUPER_ADMIN:  # Vérifie que le rôle de l'utilisateur est bien super admin.
        raise HTTPException(  # Interrompt la requête.
            status_code=status.HTTP_403_FORBIDDEN,  # Code 403 : authentifié mais non autorisé.
            detail="Permissions insuffisantes.",  # Message renvoyé au client.
        )
    return current_user  # Autorise la suite de la requête en renvoyant l'utilisateur.