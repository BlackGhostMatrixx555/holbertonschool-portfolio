"""
Routes pour les paiements.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/checkout", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    service: PaymentService = Depends(get_payment_service),
):
    """Simule le paiement d'une inscription et calcule la commission."""
    try:
        return service.process_payment(str(data.registration_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
