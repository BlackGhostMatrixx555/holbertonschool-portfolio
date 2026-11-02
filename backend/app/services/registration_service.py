"""Inscriptions publiques aux camps et suivi des présences."""
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Camp, CampStatus, Registration, User
from app.schemas.registration import RegistrationCreate
from app.services.camp_service import get_managed_camp


def register(db: Session, slug: str, payload: RegistrationCreate) -> Registration:
    """
    Inscrit un visiteur à un camp publié.

    SELECT ... FOR UPDATE verrouille la ligne du camp pendant la transaction :
    si deux personnes s'inscrivent à la dernière place au même moment,
    la seconde attend la fin de la première et voit le camp complet.
    """
    camp = db.query(Camp).filter(Camp.slug == slug).with_for_update().first()
    if camp is None or camp.status != CampStatus.PUBLISHED:
        raise NotFoundError("Camp introuvable.")

    email = payload.email.lower()
    already_registered = db.query(Registration.id).filter(
        Registration.camp_id == camp.id,
        func.lower(Registration.email) == email,
    ).first()
    if already_registered:
        raise ConflictError("Une inscription existe déjà pour cet email.")

    count = db.query(func.count(Registration.id)).filter(Registration.camp_id == camp.id).scalar()
    if count >= camp.capacity:
        raise ConflictError("Ce camp a atteint sa capacité maximale.")

    registration = Registration(
        camp_id=camp.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        comment=payload.comment,
    )
    db.add(registration)
    db.commit()  # libère aussi le verrou
    db.refresh(registration)
    return registration


def list_for_camp(db: Session, camp_id: UUID, user: User) -> list[Registration]:
    get_managed_camp(db, camp_id, user)  # contrôle d'accès
    return (
        db.query(Registration)
        .filter(Registration.camp_id == camp_id)
        .order_by(Registration.created_at.desc())
        .all()
    )


def set_attendance(db: Session, registration_id: UUID, confirmed: bool, user: User) -> Registration:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise NotFoundError("Inscription introuvable.")
    get_managed_camp(db, registration.camp_id, user)
    registration.confirmed = confirmed
    db.commit()
    db.refresh(registration)
    return registration
