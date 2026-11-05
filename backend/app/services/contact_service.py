"""Messages envoyés depuis le formulaire de contact d'une landing page."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Camp, CampStatus, ContactMessage, MessageStatus, User
from app.schemas.contact import ContactMessageCreate
from app.services.camp_service import get_managed_camp


def create_message(db: Session, slug: str, payload: ContactMessageCreate) -> ContactMessage:
    """Enregistre un message de visiteur. Seul un camp publié peut recevoir des messages."""
    camp = db.query(Camp).filter(Camp.slug == slug, Camp.status == CampStatus.PUBLISHED).first()
    if camp is None:
        raise NotFoundError("Camp introuvable.")
    message = ContactMessage(camp_id=camp.id, **payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_for_camp(db: Session, camp_id: UUID, user: User) -> list[ContactMessage]:
    """Messages d'un camp, du plus récent au plus ancien."""
    # Vérifie que l'utilisateur gère ce camp (organisateur ou super admin), sinon 403/404.
    get_managed_camp(db, camp_id, user)
    return (
        db.query(ContactMessage)
        .filter(ContactMessage.camp_id == camp_id)
        .order_by(ContactMessage.created_at.desc())
        .all()
    )


def update_status(db: Session, message_id: UUID, new_status: MessageStatus, user: User) -> ContactMessage:
    """Change le statut d'un message (non lu, lu, archivé)."""
    message = db.get(ContactMessage, message_id)
    if message is None:
        raise NotFoundError("Message introuvable.")
    # Même contrôle d'accès que pour la liste : on remonte au camp du message.
    get_managed_camp(db, message.camp_id, user)
    message.status = new_status
    db.commit()
    db.refresh(message)
    return message
