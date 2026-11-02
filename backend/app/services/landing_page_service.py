"""Création et publication de la landing page d'un camp."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CampStatus, LandingPage, User
from app.schemas.landing_page import LandingPageUpdate
from app.services.camp_service import get_managed_camp


def upsert_landing_page(db: Session, camp_id: UUID, payload: LandingPageUpdate, user: User) -> LandingPage:
    """
    Crée la landing page si elle n'existe pas, sinon la met à jour ("upsert").
    Publier la page publie aussi le camp, ce qui ouvre les inscriptions.
    """
    camp = get_managed_camp(db, camp_id, user)

    landing_page = camp.landing_page
    if landing_page is None:
        landing_page = LandingPage(camp_id=camp.id)
        db.add(landing_page)

    landing_page.season_theme = payload.season_theme
    landing_page.hero_title = payload.hero_title
    landing_page.hero_description = payload.hero_description

    if payload.publish:
        # On garde la date de première publication si la page était déjà en ligne.
        landing_page.published_at = landing_page.published_at or datetime.now(timezone.utc)
        camp.status = CampStatus.PUBLISHED
    else:
        landing_page.published_at = None
        camp.status = CampStatus.DRAFT

    db.commit()
    db.refresh(landing_page)
    return landing_page
