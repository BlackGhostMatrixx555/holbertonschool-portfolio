"""Indicateurs du tableau de bord organisateur."""
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Camp, CampStatus, Registration, User
from app.services.permissions import is_super_admin


def summary(db: Session, user: User) -> dict:
    """
    Compte les camps par statut en UNE requête SQL (agrégation avec CASE),
    puis récupère les 10 dernières inscriptions grâce à une jointure.
    """
    camps_filter = [] if is_super_admin(user) else [Camp.organizer_id == user.id]

    total, draft, published, archived = db.query(
        func.count(Camp.id),
        func.count(case((Camp.status == CampStatus.DRAFT, 1))),
        func.count(case((Camp.status == CampStatus.PUBLISHED, 1))),
        func.count(case((Camp.status == CampStatus.ARCHIVED, 1))),
    ).filter(*camps_filter).one()

    registrations = db.query(Registration).join(Camp, Registration.camp_id == Camp.id).filter(*camps_filter)

    return {
        "camps": {"total": total, "draft": draft, "published": published, "archived": archived},
        "registrations": {"total": registrations.count()},
        "recent_registrations": registrations.order_by(Registration.created_at.desc()).limit(10).all(),
    }
