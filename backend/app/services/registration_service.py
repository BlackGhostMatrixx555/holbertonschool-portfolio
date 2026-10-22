"""
Service métier pour les inscriptions.
"""
import uuid
from sqlalchemy.orm import Session

from app.models import Registration, Camp
from app.schemas.registration import RegistrationCreate


class RegistrationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, camp_id: uuid.UUID, data: RegistrationCreate) -> Registration:
        """Inscrit un visiteur à un camp, en vérifiant la capacité."""
        camp = self.db.query(Camp).filter(Camp.id == camp_id).first()
        if camp is None:
            raise ValueError("Camp introuvable.")
        
        # Vérification de la capacité
        current_count = self.db.query(Registration).filter(Registration.camp_id == camp_id).count()
        if camp.capacity > 0 and current_count >= camp.capacity:
            raise ValueError("Camp complet.")

        registration = Registration(
            camp_id=camp_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email.lower(),
            comment=data.comment,
            confirmed=data.confirmed,
        )
        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def list_for_camp(self, camp_id: uuid.UUID) -> list[Registration]:
        """Liste les inscriptions d'un camp (pour l'organisateur)."""
        return (
            self.db.query(Registration)
            .filter(Registration.camp_id == camp_id)
            .order_by(Registration.created_at.desc())
            .all()
        )

    def count_for_camp(self, camp_id: uuid.UUID) -> int:
        """Compte le nombre d'inscrits pour un camp."""
        return self.db.query(Registration).filter(Registration.camp_id == camp_id).count()
