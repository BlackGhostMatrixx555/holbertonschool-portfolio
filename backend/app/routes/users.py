"""
Routes de gestion des utilisateurs.

Réservé au super admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


# Dépendance réutilisable : seuls les super_admin peuvent passer.
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
