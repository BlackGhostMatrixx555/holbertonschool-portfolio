"""Routes du formulaire de contact (hotline)."""  # Docstring du module : routes du formulaire de contact et de la gestion des messages.
from uuid import UUID  # Type pour les identifiants passés dans les URL.

from fastapi import APIRouter, Depends, status  # APIRouter pour grouper les routes, Depends pour l'injection, status pour les codes HTTP nommés.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.contact import ContactMessageCreate, ContactMessageStatusUpdate, ContactMessageView  # Schémas d'entrée (création, changement de statut) et de sortie (message).
from app.services import contact_service  # Couche service contenant la logique métier des messages.

router = APIRouter(tags=["Contact"])  # Routeur sans préfixe, regroupé sous "Contact" dans la documentation Swagger.

@router.post("/camps/{slug}/contact-messages", response_model=ContactMessageView, status_code=status.HTTP_201_CREATED)  # Route POST : envoi d'un message via le formulaire d'un camp identifié par son slug, réponse 201.
def create_contact_message(slug: str, payload: ContactMessageCreate, db: Session = Depends(get_db)):  # Reçoit le slug, le message et la session. Aucune authentification : route publique.
    return contact_service.create_message(db, slug, payload)  # Délègue la création au service, qui retrouve le camp par son slug et enregistre le message.

@router.get("/camps/{camp_id}/contact-messages", response_model=list[ContactMessageView])  # Route GET : liste des messages reçus pour un camp, identifié par son UUID.
def list_contact_messages(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Identifiant du camp, utilisateur connecté (obligatoire) et session.
    return contact_service.list_for_camp(db, camp_id, current_user)  # Délègue au service, qui vérifie que l'utilisateur gère bien ce camp avant de renvoyer les messages.

@router.patch("/contact-messages/{message_id}", response_model=ContactMessageView)  # Route PATCH : modification partielle d'un message, ici son statut de traitement.
def update_contact_message_status(  # Met à jour le statut d'un message.
    message_id: UUID, payload: ContactMessageStatusUpdate,  # Identifiant du message et nouveau statut.
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),  # Utilisateur connecté (obligatoire) et session.
):
    return contact_service.update_status(db, message_id, payload.status, current_user)  # Délègue au service, qui vérifie les droits de l'utilisateur sur ce message avant de changer son statut.