"""
Routes HTTP pour les camps.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Camp, CampStatus, Registration, User, UserRole
from app.schemas.camp import CampCreate, CampPublicRead, CampRead, CampUpdate
from app.schemas.registration import RegistrationCreate, RegistrationRead
from app.services.camp_service import CampService
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/camps", tags=["camps"])

def get_camp_service(db: Session = Depends(get_db)) -> CampService:
    return CampService(db)

def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    return RegistrationService(db)

# ---------------------------------------------------------------------------
# CRUD Camps
# ---------------------------------------------------------------------------
@router.post("", response_model=CampRead, status_code=status.HTTP_201_CREATED)
def create_camp(data: CampCreate, service: CampService = Depends(get_camp_service), current_user: User = Depends(get_current_user)):
    return service.create(data, organizer_id=current_user.id)

@router.get("", response_model=list[CampRead])
def list_camps(status_filter: CampStatus | None = Query(None, alias="status"), organizer_id: uuid.UUID | None = Query(None), service: CampService = Depends(get_camp_service)):
    return service.list(status=status_filter, organizer_id=organizer_id)

@router.patch("/{camp_id}", response_model=CampRead)
def update_camp(camp_id: uuid.UUID, data: CampUpdate, service: CampService = Depends(get_camp_service), current_user: User = Depends(get_current_user)):
    camp = service.get_by_id(camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier ce camp.")
    return service.update(camp, data)

@router.delete("/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camp(camp_id: uuid.UUID, service: CampService = Depends(get_camp_service), current_user: User = Depends(get_current_user)):
    camp = service.get_by_id(camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer ce camp.")
    service.delete(camp)
    return None

# ---------------------------------------------------------------------------
# Landing Page (Vue publique avec compteur)
# ---------------------------------------------------------------------------
@router.get("/{slug}/public", response_model=CampPublicRead)
def get_public_camp(slug: str, service: CampService = Depends(get_camp_service), reg_service: RegistrationService = Depends(get_registration_service)):
    camp = service.get_by_slug(slug)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    
    # On construit la réponse manuellement pour y injecter le compteur
    response_data = CampPublicRead.model_validate(camp).model_dump()
    response_data["registration_count"] = reg_service.count_for_camp(camp.id)
    return response_data

# ---------------------------------------------------------------------------
# Inscriptions (Visiteurs & Organisateurs)
# ---------------------------------------------------------------------------
@router.post("/{camp_id}/registrations", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_to_camp(camp_id: uuid.UUID, data: RegistrationCreate, reg_service: RegistrationService = Depends(get_registration_service)):
    """Inscription publique (aucune authentification requise)."""
    try:
        return reg_service.create(camp_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{camp_id}/registrations", response_model=list[RegistrationRead])
def list_registrations(camp_id: uuid.UUID, db: Session = Depends(get_db), reg_service: RegistrationService = Depends(get_registration_service), current_user: User = Depends(get_current_user)):
    """Liste des inscrits. Réservé aux organisateurs du camp, directeurs et super admin."""
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'avez pas le droit de voir les inscrits de ce camp.")
    
    return reg_service.list_for_camp(camp_id)

@router.delete("/{camp_id}/registrations/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registration(camp_id: uuid.UUID, registration_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Supprime une inscription (Organisateur du camp / Directeur / Super Admin)."""
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Action non autorisée.")
    
    reg = db.query(Registration).filter(Registration.id == registration_id, Registration.camp_id == camp_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    
    db.delete(reg)
    db.commit()
    return None
