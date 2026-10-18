from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import Camp, CampStatus, Registration, User, UserRole

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    camp_query = db.query(Camp)
    if current_user.role != UserRole.SUPER_ADMIN:
        camp_query = camp_query.filter(Camp.organizer_id == current_user.id)
    camp_ids = [row[0] for row in camp_query.with_entities(Camp.id).all()]

    camp_counts = {
        "total": len(camp_ids),
        "draft": camp_query.filter(Camp.status == CampStatus.DRAFT).count(),
        "published": camp_query.filter(Camp.status == CampStatus.PUBLISHED).count(),
        "archived": camp_query.filter(Camp.status == CampStatus.ARCHIVED).count(),
    }
    registration_query = db.query(Registration).filter(Registration.camp_id.in_(camp_ids))
    registration_count = registration_query.count() if camp_ids else 0
    recent_registrations = registration_query.order_by(
        Registration.created_at.desc()
    ).limit(10).all() if camp_ids else []

    return {
        "camps": camp_counts,
        "registrations": {"total": registration_count},
        "recent_registrations": [
            {
                "id": str(registration.id),
                "camp_id": str(registration.camp_id),
                "first_name": registration.first_name,
                "last_name": registration.last_name,
                "email": registration.email,
                "created_at": registration.created_at,
            }
            for registration in recent_registrations
        ],
    }