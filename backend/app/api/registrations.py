"""Routes des inscriptions."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.registration import AttendanceUpdate, RegistrationCreate, RegistrationView
from app.services import registration_service

router = APIRouter(tags=["Inscriptions"])


@router.post("/camps/{slug}/registrations", response_model=RegistrationView, status_code=status.HTTP_201_CREATED)
def register_for_camp(slug: str, payload: RegistrationCreate, db: Session = Depends(get_db)):
    """Inscription publique depuis la landing page (sans compte)."""
    return registration_service.register(db, slug, payload)


@router.get("/camps/{camp_id}/registrations", response_model=list[RegistrationView])
def list_camp_registrations(
    camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return registration_service.list_for_camp(db, camp_id, current_user)


@router.patch("/registrations/{registration_id}/attendance", response_model=RegistrationView)
def update_attendance(
    registration_id: UUID, payload: AttendanceUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    return registration_service.set_attendance(db, registration_id, payload.confirmed, current_user)
