"""Routes des camps : espace organisateur et vues publiques."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import CampStatus, User
from app.schemas.camp import CampInput, CampPublicView, CampView
from app.services import camp_service

router = APIRouter(tags=["Camps"])


# ---- Routes publiques (sans authentification) ------------------------------

@router.get("/public/camps", response_model=list[CampPublicView])
def list_public_camps(db: Session = Depends(get_db)):
    """Liste des camps publiés, pour la page d'accueil."""
    return camp_service.list_public_camps(db)


@router.get("/camps/{slug}/public", response_model=CampPublicView)
def get_public_camp(slug: str, db: Session = Depends(get_db)):
    """Landing page d'un camp publié, retrouvé par son slug."""
    return camp_service.get_public_camp(db, slug)


# ---- Routes organisateur (jeton JWT obligatoire) ----------------------------

@router.post("/camps", response_model=CampView, status_code=status.HTTP_201_CREATED)
def create_camp(
    payload: CampInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return camp_service.create_camp(db, payload, current_user)


@router.get("/camps", response_model=list[CampView])
def list_camps(
    status_filter: CampStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return camp_service.list_camps_for(db, current_user, status_filter)


@router.get("/camps/{camp_id}", response_model=CampView)
def get_camp(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Détail d'un camp géré (formulaire de modification côté front-end)."""
    return camp_service.get_managed_camp(db, camp_id, current_user)


@router.patch("/camps/{camp_id}", response_model=CampView)
def update_camp(
    camp_id: UUID,
    payload: CampInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return camp_service.update_camp(db, camp_id, payload, current_user)


@router.delete("/camps/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camp(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    camp_service.delete_camp(db, camp_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
