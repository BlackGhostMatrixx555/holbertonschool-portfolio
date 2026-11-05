"""Route de création / publication de la landing page d'un camp."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.landing_page import LandingPageUpdate, LandingPageView
from app.services import landing_page_service

router = APIRouter(tags=["Landing pages"])


@router.put("/camps/{camp_id}/landing-page", response_model=LandingPageView)
def update_landing_page(
    camp_id: UUID, payload: LandingPageUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    # PUT : la landing page est remplacée entièrement (opération idempotente).
    return landing_page_service.upsert_landing_page(db, camp_id, payload, current_user)
