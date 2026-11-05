"""Route du tableau de bord organisateur."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.dashboard import DashboardSummary
from app.services import dashboard_service

router = APIRouter(tags=["Tableau de bord"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chiffres clés : un organisateur voit ses camps, le super admin voit tout."""
    return dashboard_service.summary(db, current_user)
