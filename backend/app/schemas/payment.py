"""
Schémas Pydantic pour les paiements.
"""
# uuid : module pour manipuler les identifiants uniques (UUID)
import uuid
# BaseModel : classe de base des schémas Pydantic
# ConfigDict : permet de configurer le comportement d'un schéma
from pydantic import BaseModel, ConfigDict
# PaymentStatus : énumération des états possibles d'un paiement (défini dans le modèle de base de données)
from app.models.payment import PaymentStatus


# Schéma des données ENTRANTES : ce que le client envoie pour lancer un paiement
class PaymentCreate(BaseModel):
    """Données envoyées pour déclencher un paiement."""
    # Identifiant de l'inscription à payer : c'est la seule information fournie par le client
    registration_id: uuid.UUID


# Schéma des données SORTANTES : ce que l'API renvoie pour décrire un paiement
class PaymentRead(BaseModel):
    """Paiement tel que renvoyé par l'API."""
    # from_attributes=True : permet de construire ce schéma directement depuis un objet SQLAlchemy (modèle de la base)
    model_config = ConfigDict(from_attributes=True)

    # Identifiant unique du paiement, généré par le serveur
    id: uuid.UUID
    # Identifiant de l'inscription concernée par ce paiement
    registration_id: uuid.UUID
    # Montant total payé par le participant (entier, probablement en centimes)
    amount_total: int
    # Part prélevée par la plateforme (commission), même unité que le montant total
    platform_fee: int
    # Part reversée à l'organisateur du camp, même unité que le montant total
    organizer_amount: int
    # État du paiement (par exemple en attente, réussi, échoué), selon l'énumération PaymentStatus
    status: PaymentStatus
    # Identifiant de la transaction côté prestataire de paiement : None tant que le paiement n'a pas été traité
    transaction_id: str | None
