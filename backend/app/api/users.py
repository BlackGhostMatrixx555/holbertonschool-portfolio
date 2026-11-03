"""Comptes : profil personnel (/users/me) et administration (super admin)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_super_admin
from app.db.session import get_db
from app.models import User
from app.schemas.user import ProfileUpdate, UserCreate, UserRoleUpdate, UserStatusUpdate, UserView
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


# ---- Son propre compte (tout utilisateur connecté) ------------------------------
# Déclarées AVANT /{user_id} : sinon "me" serait lu comme un identifiant.

@router.patch("/me", response_model=UserView)
def update_my_profile(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.update_profile(db, current_user, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_service.delete_own_account(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- Administration (super admin) ---------------------------------------------

@router.get("", response_model=list[UserView])
def list_users(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return user_service.list_users(db)


@router.post("", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return user_service.create_user(db, payload)


@router.patch("/{user_id}/role", response_model=UserView)
def update_user_role(
    user_id: UUID, payload: UserRoleUpdate,
    current_user: User = Depends(require_super_admin), db: Session = Depends(get_db),
):
    return user_service.update_role(db, user_id, payload.role, current_user)


@router.patch("/{user_id}/status", response_model=UserView)
def update_user_status(
    user_id: UUID, payload: UserStatusUpdate,
    current_user: User = Depends(require_super_admin), db: Session = Depends(get_db),
):
    return user_service.update_status(db, user_id, payload.status, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    user_service.delete_user(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
