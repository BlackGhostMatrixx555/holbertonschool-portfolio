"""
Service métier pour le chatbot et les messages de contact.
"""
from sqlalchemy.orm import Session

from app.models import ContactMessage, ContactChannel
from app.schemas.chat import ChatRequest, ContactMessageCreate


class ChatService:
    """Regroupe les opérations liées au chatbot et à la hotline."""

    def __init__(self, db: Session):
        self.db = db

    def process_message(self, data: ChatRequest) -> str:
        """Traite un message et renvoie une réponse.
        
        Pour le MVP, on utilise un système à base de règles (Mock).
        En V2, on remplacera cette méthode par un appel à l'API Claude/OpenAI.
        """
        msg = data.message.lower()

        # Logique simple de détection de mots-clés
        if "prix" in msg or "tarif" in msg or "coût" in msg:
            reply = "Les tarifs varient selon les camps. Veuillez consulter la page du camp ou contacter notre hotline."
        elif "date" in msg or "quand" in msg:
            reply = "Les dates sont indiquées sur la landing page de chaque camp."
        elif "inscription" in msg or "inscrire" in msg:
            reply = "Pour vous inscrire, remplissez le formulaire sur la page du camp qui vous intéresse."
        elif "âge" in msg or "age" in msg:
            reply = "Chaque camp a ses propres critères d'âge. Ils sont listés dans la section 'Modalités'."
        else:
            reply = "Je suis un assistant virtuel. Pour une question spécifique, n'hésitez pas à utiliser la hotline."

        # On enregistre le message en base pour la traçabilité
        contact_msg = ContactMessage(
            camp_id=data.camp_id,
            message=data.message,
            channel=ContactChannel.CHATBOT,
        )
        self.db.add(contact_msg)
        self.db.commit()

        return reply

    def create_contact_message(self, data: ContactMessageCreate) -> ContactMessage:
        """Enregistre un message envoyé via la hotline (formulaire de contact)."""
        msg = ContactMessage(
            camp_id=data.camp_id,
            name=data.name,
            email=data.email,
            message=data.message,
            channel=ContactChannel.HOTLINE,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
