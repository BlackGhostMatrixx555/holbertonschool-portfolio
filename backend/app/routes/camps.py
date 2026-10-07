"""
Routes HTTP pour les camps.

Endpoints :
  - POST   /api/camps                : créer un camp (organisateur connecté).
  - GET    /api/camps                : lister les camps (filtres optionnels).
  - GET    /api/camps/{slug}/public  : consulter un camp publiquement via son slug.
  - PATCH  /api/camps/{id}           : modifier un camp (organisateur/admin).
  - DELETE /api/camps/{id}           : supprimer un camp (organisateur/admin).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Camp, CampStatus, User
from app.schemas.camp import CampCreate, CampPublicRead, CampRead, CampUpdate
from app.services.camp_service import CampService

router = APIRouter(prefix="/camps", tags=["camps"])


def get_camp_service(db: Session = Depends(get_db)) -> CampService:
    """Fournit une instance de CampService liée à la session courante."""
    return CampService(db)


# ---------------------------------------------------------------------------
# POST /api/camps — créer un camp
# ---------------------------------------------------------------------------
@router.post("", response_model=CampRead, status_code=status.HTTP_201_CREATED)
def create_camp(
    data: CampCreate,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    """Crée un camp appartenant à l'utilisateur connecté."""
    camp = service.create(data, organizer_id=current_user.id)
    return camp


# ---------------------------------------------------------------------------
# GET /api/camps — lister les camps
# ---------------------------------------------------------------------------
@router.get("", response_model=list[CampRead])
def list_camps(
    status_filter: CampStatus | None = Query(None, alias="status"),
    organizer_id: uuid.UUID | None = Query(None),
    service: CampService = Depends(get_camp_service),
):
    """Liste les camps, avec filtres optionnels par statut et organisateur."""
    return service.list(status=status_filter, organizer_id=organizer_id)


# ---------------------------------------------------------------------------
# GET /api/camps/{slug}/public — vue publique
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# PATCH /api/camps/{id} — modifier un camp
# ---------------------------------------------------------------------------
@router.patch("/{camp_id}", response_model=CampRead)
def update_camp(
    camp_id: uuid.UUID,
    data: CampUpdate,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    """Met à jour partiellement un camp.

    Seuls les champs fournis dans le corps sont modifiés. Les autres restent
    inchangés (comportement PATCH standard).

    Règles métier (à étendre en Étape 5 avec la gestion des rôles) :
      - Le super admin peut modifier n'importe quel camp.
      - L'organisateur ne peut modifier que ses propres camps.
    """
    camp = service.get_by_id(camp_id)
    if camp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camp introuvable.",
        )

    # Vérification des droits (temporaire : avant Étape 5)
    if camp.organizer_id != current_user.id and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier ce camp.",
        )

    updated = service.update(camp, data)
    return updated


# ---------------------------------------------------------------------------
# DELETE /api/camps/{id} — supprimer un camp
# ---------------------------------------------------------------------------
@router.delete("/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camp(
    camp_id: uuid.UUID,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    """Supprime un camp et toutes ses données liées (modalités, landing page,
    inscriptions) grâce au cascade configuré dans les modèles SQLAlchemy.

    Mêmes règles métier que PATCH.
    """
    camp = service.get_by_id(camp_id)
    if camp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camp introuvable.",
        )

    if camp.organizer_id != current_user.id and current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer ce camp.",
        )

    service.delete(camp)
    return None
