"""
Routes de gestion des utilisateurs.

- POST   /api/users          : créer un utilisateur (super admin).
- GET    /api/users          : lister les utilisateurs (super admin).
- DELETE /api/users/me       : supprimer son propre compte (self-service).
- DELETE /api/users/{id}     : supprimer un utilisateur (super admin).
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


# Dépendances réutilisables
super_admin_only = require_role(UserRole.SUPER_ADMIN)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
    _: User = Depends(super_admin_only),
):
    """Crée un utilisateur. Réservé au super admin."""
    if service.get_by_email(data.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà.",
        )
    return service.create(data)


@router.get("", response_model=list[UserRead])
def list_users(
    service: UserService = Depends(get_user_service),
    _: User = Depends(super_admin_only),
):
    """Liste tous les utilisateurs. Réservé au super admin."""
    return service.list()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permet à un utilisateur de supprimer son propre compte.

    ⚠️ Le Super Admin est éternel et ne peut jamais être supprimé.
    ⚠️ Si l'utilisateur a créé des camps, la contrainte ON DELETE RESTRICT
    de PostgreSQL empêchera la suppression (400).
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le Super Admin est éternel et ne peut pas être supprimé.",
        )
    try:
        db.delete(current_user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer le compte : des données y sont encore rattachées.",
        )
    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(super_admin_only),
):
    """Supprime n'importe quel utilisateur par son ID. Réservé au Super Admin."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le Super Admin ne peut pas être supprimé.",
        )
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer : des données y sont rattachées.",
        )
    return None
