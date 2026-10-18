import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import (
    Camp,
    CampStatus,
    ContactChannel,
    ContactMessage,
    MessageStatus,
    User,
    UserRole,
)

router = APIRouter()


class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    message: str
    channel: ContactChannel = ContactChannel.HOTLINE


class ContactMessageStatusUpdate(BaseModel):
    status: MessageStatus


class ContactMessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camp_id: uuid.UUID
    name: str
    email: EmailStr
    message: str
    channel: ContactChannel
    status: MessageStatus


@router.post("/camps/{slug}/contact-messages", response_model=ContactMessageView, status_code=201)
def create_contact_message(
    slug: str,
    payload: ContactMessageCreate,
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).filter(
        Camp.slug == slug,
        Camp.status == CampStatus.PUBLISHED,
    ).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")

    contact_message = ContactMessage(camp_id=camp.id, **payload.model_dump())
    db.add(contact_message)
    db.commit()
    db.refresh(contact_message)
    return contact_message


@router.get("/camps/{camp_id}/contact-messages", response_model=list[ContactMessageView])
def list_contact_messages(
    camp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    if camp.organizer_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")
    return db.query(ContactMessage).filter(ContactMessage.camp_id == camp_id).order_by(
        ContactMessage.created_at.desc()
    ).all()


@router.patch("/contact-messages/{message_id}", response_model=ContactMessageView)
def update_contact_message_status(
    message_id: uuid.UUID,
    payload: ContactMessageStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact_message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if contact_message is None:
        raise HTTPException(status_code=404, detail="Message introuvable.")
    camp = db.query(Camp).filter(Camp.id == contact_message.camp_id).first()
    if camp.organizer_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")
    contact_message.status = payload.status
    db.commit()
    db.refresh(contact_message)
    return contact_message