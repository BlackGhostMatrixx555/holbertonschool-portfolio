"""Routes du formulaire de contact (hotline)."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.contact import ContactMessageCreate, ContactMessageStatusUpdate, ContactMessageView
from app.services import contact_service

router = APIRouter(tags=["Contact"])


@router.post("/camps/{slug}/contact-messages", response_model=ContactMessageView, status_code=status.HTTP_201_CREATED)
def create_contact_message(slug: str, payload: ContactMessageCreate, db: Session = Depends(get_db)):
    """Public : un visiteur envoie un message depuis la landing page."""
    return contact_service.create_message(db, slug, payload)


@router.get("/camps/{camp_id}/contact-messages", response_model=list[ContactMessageView])
def list_contact_messages(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Organisateur du camp ou super admin : liste des messages."""
    return contact_service.list_for_camp(db, camp_id, current_user)


@router.patch("/contact-messages/{message_id}", response_model=ContactMessageView)
def update_contact_message_status(
    message_id: UUID, payload: ContactMessageStatusUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Organisateur du camp ou super admin : marquer comme lu ou archivé."""
    return contact_service.update_status(db, message_id, payload.status, current_user)
