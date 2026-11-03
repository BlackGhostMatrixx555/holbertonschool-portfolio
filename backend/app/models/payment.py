"""
Modèle Payment — historique des transactions et des commissions.
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid
# enum : module standard Python pour créer des énumérations (ensembles de valeurs fixes)
import enum
# Column : déclare une colonne ; String, Integer, Enum, DateTime, ForeignKey : types et contraintes SQL ; func : fonctions SQL côté base
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, func
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles
from sqlalchemy.orm import relationship
# Base : classe mère de tous les modèles
from app.database import Base


# Énumération des statuts possibles d'un paiement
# Hérite de str : les valeurs se comportent comme des chaînes, pratique pour la sérialisation JSON
class PaymentStatus(str, enum.Enum):
    # Paiement créé mais pas encore validé
    PENDING = "pending"
    # Paiement accepté et encaissé
    SUCCESS = "success"
    # Paiement refusé ou en échec
    FAILED = "failed"


# Déclaration de la classe Payment, qui correspond à la table payments
class Payment(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "payments"

    # Identifiant unique du paiement, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Lien vers l'inscription payée : clé étrangère vers registrations.id
    registration_id = Column(
        UUID(as_uuid=True),
        # ondelete="CASCADE" : si l'inscription disparaît, son paiement disparaît aussi
        ForeignKey("registrations.id", ondelete="CASCADE"),
        # Obligatoire : un paiement doit toujours être rattaché à une inscription
        nullable=False,
        # Index pour retrouver rapidement le paiement d'une inscription
        index=True,
    )
    # Montant total payé par le visiteur, en entier (souvent en centimes pour éviter les erreurs d'arrondi)
    amount_total = Column(Integer, nullable=False)      # Montant total payé par le visiteur
    # Commission prélevée par la plateforme
    platform_fee = Column(Integer, nullable=False)      # Ta commission (ex: 10%)
    # Montant net revenant à l'organisateur
    organizer_amount = Column(Integer, nullable=False)  # Montant pour l'organisateur
    # Statut du paiement, stocké comme ENUM ; PENDING par défaut
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    # Identifiant renvoyé par le prestataire de paiement (ici simulé, Stripe en production)
    transaction_id = Column(String(255), nullable=True)  # ID de transaction Stripe (mock)
    # Date de création du paiement, remplie automatiquement par la base
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relation
    # Inscription associée à ce paiement (lien inverse défini dans Registration)
    registration = relationship("Registration", back_populates="payment")

    # Représentation textuelle de l'objet pour le débogage et les logs
    def __repr__(self) -> str:
        # Affiche l'identifiant et la valeur du statut, par exemple <Payment ... - pending>
        return f"<Payment {self.id} - {self.status.value}>"
