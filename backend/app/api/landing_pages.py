import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import Camp, CampStatus, LandingPage, SeasonTheme, User, UserRole

router = APIRouter()


class LandingPageUpdate(BaseModel):
    season_theme: SeasonTheme
    hero_title: str
    hero_description: str | None = None
    publish: bool = False


class LandingPageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camp_id: uuid.UUID
    season_theme: SeasonTheme
    hero_title: str
    hero_description: str | None
    published_at: datetime | None


@router.put("/camps/{camp_id}/landing-page", response_model=LandingPageView)
def update_landing_page(
    camp_id: uuid.UUID,
    payload: LandingPageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    if camp.organizer_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")

    landing_page = db.query(LandingPage).filter(LandingPage.camp_id == camp.id).first()
    if landing_page is None:
        landing_page = LandingPage(camp_id=camp.id)
        db.add(landing_page)
    landing_page.season_theme = payload.season_theme
    landing_page.hero_title = payload.hero_title
    landing_page.hero_description = payload.hero_description
    landing_page.published_at = datetime.now(timezone.utc) if payload.publish else None
    camp.status = CampStatus.PUBLISHED if payload.publish else CampStatus.DRAFT

    db.commit()
    db.refresh(landing_page)
    return landing_page