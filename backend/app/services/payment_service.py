"""
Service métier pour les paiements (Mock).

Simule un paiement réussi et calcule la commission de la plateforme (10%).
En production, on remplacerait cette logique par Stripe Connect.
"""
from sqlalchemy.orm import Session
from app.models import Payment, PaymentStatus, Registration, Camp


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def process_payment(self, registration_id: str) -> Payment:
        """Simule un paiement et calcule la commission."""
        registration = self.db.query(Registration).filter(Registration.id == registration_id).first()
        if not registration:
            raise ValueError("Inscription introuvable.")

        camp = self.db.query(Camp).filter(Camp.id == registration.camp_id).first()
        if not camp:
            raise ValueError("Camp introuvable.")

        # Calculs
        amount_total = camp.price
        platform_fee = int(amount_total * 0.10)  # 10% de commission pour la plateforme
        organizer_amount = amount_total - platform_fee

        # Simulation Stripe (Mock)
        # En production : stripe.checkout.Session.create(...)
        transaction_id = f"mock_txn_{registration.id.hex[:8]}"

        payment = Payment(
            registration_id=registration.id,
            amount_total=amount_total,
            platform_fee=platform_fee,
            organizer_amount=organizer_amount,
            status=PaymentStatus.SUCCESS,
            transaction_id=transaction_id,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
