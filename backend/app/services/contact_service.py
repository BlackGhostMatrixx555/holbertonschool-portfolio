"""Messages envoyés depuis le formulaire de contact d'une landing page."""
from uuid import UUID  # Type des identifiants (camp, message).

from sqlalchemy.orm import Session  # Session SQLAlchemy pour interroger et modifier la base.

from app.core.exceptions import NotFoundError  # Erreur métier renvoyée quand une ressource n'existe pas (traduite en 404).
from app.models import Camp, CampStatus, ContactMessage, MessageStatus, User  # Modèles et énumérations utilisés.
from app.schemas.contact import ContactMessageCreate  # Schéma des données du formulaire de contact.
from app.services.camp_service import get_managed_camp  # Récupère un camp en vérifiant que l'utilisateur peut le gérer.

def create_message(db: Session, slug: str, payload: ContactMessageCreate) -> ContactMessage:  # Enregistre un message envoyé par un visiteur (accès public).
    camp = db.query(Camp).filter(Camp.slug == slug, Camp.status == CampStatus.PUBLISHED).first()  # Cherche un camp publié correspondant au slug.
    if camp is None:  # Camp absent ou non publié : on ne peut pas recevoir de message.
        raise NotFoundError("Camp introuvable.")
    message = ContactMessage(camp_id=camp.id, **payload.model_dump())  # Crée le message lié au camp à partir des champs du formulaire.
    db.add(message)  # Prépare l'insertion en base.
    db.commit()  # Enregistre le message.
    db.refresh(message)  # Recharge le message depuis la base (ex. identifiant, date de création).
    return message  # Renvoie le message créé.

def list_for_camp(db: Session, camp_id: UUID, user: User) -> list[ContactMessage]:  # Liste les messages reçus pour un camp.
    get_managed_camp(db, camp_id, user)  # Vérifie que l'utilisateur a le droit de gérer ce camp (lève une erreur sinon).
    return (
        db.query(ContactMessage)
        .filter(ContactMessage.camp_id == camp_id)  # Uniquement les messages de ce camp.
        .order_by(ContactMessage.created_at.desc())  # Du plus récent au plus ancien.
        .all()
    )

def update_status(db: Session, message_id: UUID, new_status: MessageStatus, user: User) -> ContactMessage:  # Change le statut d'un message (ex. lu, traité).
    message = db.get(ContactMessage, message_id)  # Récupère le message par son identifiant.
    if message is None:  # Message inexistant.
        raise NotFoundError("Message introuvable.")
    get_managed_camp(db, message.camp_id, user)  # Vérifie que l'utilisateur gère le camp auquel appartient le message.
    message.status = new_status  # Applique le nouveau statut.
    db.commit()  # Enregistre la modification.
    db.refresh(message)  # Recharge le message à jour.
    return message  # Renvoie le message modifié.