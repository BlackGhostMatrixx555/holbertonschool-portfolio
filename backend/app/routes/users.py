"""
Routes de gestion des utilisateurs.

- POST   /api/users          : créer un utilisateur (super admin).
- GET    /api/users          : lister les utilisateurs (super admin).
- DELETE /api/users/me       : supprimer son propre compte (self-service).
- DELETE /api/users/{id}     : supprimer un utilisateur (super admin).
"""
# uuid : pour typer et manipuler les identifiants des utilisateurs
import uuid
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données par requête
from app.database import get_db
# get_current_user : renvoie l'utilisateur connecté ; require_role : vérifie qu'il possède un rôle donné
from app.dependencies import get_current_user, require_role
# User : modèle utilisateur ; UserRole : énumération des rôles (SUPER_ADMIN, ORGANISATEUR...)
from app.models import User, UserRole
# UserCreate : schéma d'entrée pour créer un utilisateur ; UserRead : schéma de sortie
from app.schemas.user import UserCreate, UserRead
# UserService : contient la logique métier liée aux utilisateurs
from app.services.user_service import UserService

# Groupe de routes préfixé par /users (donc /api/users une fois branché dans main.py), rangé sous le tag "users"
router = APIRouter(prefix="/users", tags=["users"])


# Fabrique du service : FastAPI lui passe automatiquement la session de base de données
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    # On renvoie un service branché sur cette session
    return UserService(db)


# Dépendance réutilisable : une fabrique qui exige le rôle SUPER_ADMIN, à brancher dans les routes
super_admin_only = require_role(UserRole.SUPER_ADMIN)


# Route POST /api/users : crée un utilisateur, réservée au super admin
@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    # Corps de la requête, validé automatiquement par le schéma UserCreate
    data: UserCreate,
    # Service utilisateur injecté automatiquement
    service: UserService = Depends(get_user_service),
    # Vérifie que l'appelant est super admin ; "_" indique qu'on ne se sert pas de la valeur renvoyée
    _: User = Depends(super_admin_only),
):
    """Crée un utilisateur. Réservé au super admin."""
    # Anti-doublon : si l'email existe déjà, on renvoie 409 Conflict
    if service.get_by_email(data.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà.",
        )
    # Création effective ; la réponse est filtrée par UserRead (le mot de passe n'est jamais renvoyé)
    return service.create(data)


# Route GET /api/users : liste tous les utilisateurs, réservée au super admin
@router.get("", response_model=list[UserRead])
def list_users(
    # Service utilisateur injecté automatiquement
    service: UserService = Depends(get_user_service),
    # Accès réservé au super admin
    _: User = Depends(super_admin_only),
):
    """Liste tous les utilisateurs. Réservé au super admin."""
    # Renvoie la liste, chaque élément étant converti en UserRead
    return service.list()


# Route DELETE /api/users/me : l'utilisateur supprime son propre compte
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    # Session de base de données, nécessaire pour effectuer la suppression
    db: Session = Depends(get_db),
    # Utilisateur connecté, identifié par son JWT : il ne peut agir que sur son propre compte
    current_user: User = Depends(get_current_user),
):
    """Permet à un utilisateur de supprimer son propre compte.

    ⚠️ Le Super Admin est éternel et ne peut jamais être supprimé.
    ⚠️ Si l'utilisateur a créé des camps, la contrainte ON DELETE RESTRICT
    de PostgreSQL empêchera la suppression (400).
    """
    # Protection : le super admin ne peut pas supprimer son propre compte
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le Super Admin est éternel et ne peut pas être supprimé.",
        )
    # On tente la suppression ; si la base refuse (données rattachées), on annule proprement
    try:
        db.delete(current_user)
        db.commit()
    except Exception:
        # Annule la transaction pour ne pas laisser la session dans un état incohérent
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer le compte : des données y sont encore rattachées.",
        )
    # 204 No Content : suppression réussie, pas de corps de réponse
    return None


# Route DELETE /api/users/{id} : le super admin supprime un utilisateur précis
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    # Identifiant lu dans l'URL et converti automatiquement en UUID (erreur 422 si le format est invalide)
    user_id: uuid.UUID,
    # Session de base de données
    db: Session = Depends(get_db),
    # Accès réservé au super admin
    _: User = Depends(super_admin_only),
):
    """Supprime n'importe quel utilisateur par son ID. Réservé au Super Admin."""
    # Recherche directe par clé primaire
    user = db.get(User, user_id)
    # Si aucun utilisateur ne correspond, erreur 404
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )
    # Protection : on ne peut jamais supprimer un super admin, même par cette route
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le Super Admin ne peut pas être supprimé.",
        )
    # Suppression avec gestion d'erreur identique à delete_my_account
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer : des données y sont rattachées.",
        )
    # 204 No Content : suppression réussie
    return None
