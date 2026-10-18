import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import Camp, CampStatus, Registration, User

router = APIRouter()


class RegistrationCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    comment: str | None = None


class RegistrationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camp_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    comment: str | None
    confirmed: bool


class AttendanceUpdate(BaseModel):
    confirmed: bool


def _owned_camp(db: Session, camp_id: uuid.UUID, user: User) -> Camp:
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    if camp.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")
    return camp


@router.post(
    "/camps/{slug}/registrations",
    response_model=RegistrationView,
    status_code=status.HTTP_201_CREATED,
)
def register_for_camp(
    slug: str,
    payload: RegistrationCreate,
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).filter(Camp.slug == slug).with_for_update().first()
    if camp is None or camp.status != CampStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Camp introuvable.")

    existing = db.query(Registration.id).filter(
        Registration.camp_id == camp.id,
        func.lower(Registration.email) == payload.email.lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Une inscription existe déjà pour cet email.")

    registration_count = db.query(func.count(Registration.id)).filter(
        Registration.camp_id == camp.id
    ).scalar()
    if registration_count >= camp.capacity:
        raise HTTPException(status_code=409, detail="Ce camp a atteint sa capacité maximale.")

    registration = Registration(camp_id=camp.id, **payload.model_dump())
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


@router.get(
    "/camps/{camp_id}/registrations",
    response_model=list[RegistrationView],
)
def list_camp_registrations(
    camp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_camp(db, camp_id, current_user)
    return db.query(Registration).filter(Registration.camp_id == camp_id).order_by(
        Registration.created_at.desc()
    ).all()


@router.patch("/registrations/{registration_id}/attendance", response_model=RegistrationView)
def update_attendance(
    registration_id: uuid.UUID,
    payload: AttendanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if registration is None:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    _owned_camp(db, registration.camp_id, current_user)
    registration.confirmed = payload.confirmed
    db.commit()
    db.refresh(registration)
    return registration