"""Administration des comptes : réservée au super admin."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_super_admin
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserRoleUpdate, UserStatusUpdate, UserView
from app.services import user_service

# La dépendance require_super_admin est appliquée à TOUTES les routes du routeur.
router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.get("", response_model=list[UserView])
def list_users(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return user_service.list_users(db)


@router.post("", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return user_service.create_user(db, payload)


@router.patch("/{user_id}/role", response_model=UserView)
def update_user_role(
    user_id: UUID, payload: UserRoleUpdate,
    _: User = Depends(require_super_admin), db: Session = Depends(get_db),
):
    return user_service.update_role(db, user_id, payload.role)


@router.patch("/{user_id}/status", response_model=UserView)
def update_user_status(
    user_id: UUID, payload: UserStatusUpdate,
    current_user: User = Depends(require_super_admin), db: Session = Depends(get_db),
):
    return user_service.update_status(db, user_id, payload.status, current_user)
