"""
Routes HTTP pour les camps.

Trois endpoints pour l'instant :
  - POST /api/camps                : créer un camp (organisateur connecté).
  - GET  /api/camps                : lister les camps (filtres optionnels).
  - GET  /api/camps/{slug}/public  : consulter un camp publiquement via son slug.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Camp, CampStatus, User
from app.schemas.camp import CampCreate, CampPublicRead, CampRead
from app.services.camp_service import CampService

router = APIRouter(prefix="/camps", tags=["camps"])


def get_camp_service(db: Session = Depends(get_db)) -> CampService:
    """Fournit une instance de CampService liée à la session courante."""
    return CampService(db)


@router.post("", response_model=CampRead, status_code=status.HTTP_201_CREATED)
def create_camp(
    data: CampCreate,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    """Crée un camp appartenant à l'utilisateur connecté."""
    camp = service.create(data, organizer_id=current_user.id)
    return camp


@router.get("", response_model=list[CampRead])
def list_camps(
    status_filter: CampStatus | None = Query(None, alias="status"),
    organizer_id: uuid.UUID | None = Query(None),
    service: CampService = Depends(get_camp_service),
):
    """Liste les camps, avec filtres optionnels par statut et organisateur."""
    return service.list(status=status_filter, organizer_id=organizer_id)


@router.get("/{slug}/public", response_model=CampPublicRead)
def get_public_camp(
    slug: str,
    service: CampService = Depends(get_camp_service),
):
    """Récupère un camp via son slug, pour la landing page publique."""
    camp = service.get_by_slug(slug)
    if camp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camp introuvable.",
        )
    return camp
