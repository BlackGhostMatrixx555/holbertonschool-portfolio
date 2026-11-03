"""
Routes pour les paiements.
"""
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données par requête
from app.database import get_db
# PaymentCreate : schéma d'entrée (l'inscription à payer) ; PaymentRead : schéma de sortie (le paiement créé)
from app.schemas.payment import PaymentCreate, PaymentRead
# PaymentService : contient la logique de paiement et de calcul de commission
from app.services.payment_service import PaymentService

# Groupe de routes préfixé par /payments, rangé sous le tag "payments" dans la doc Swagger
router = APIRouter(prefix="/payments", tags=["payments"])


# Fabrique du service : FastAPI lui passe automatiquement la session de base de données
def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    # On renvoie un service branché sur cette session
    return PaymentService(db)


# Route POST /payments/checkout : déclenche le paiement d'une inscription, renvoie 201 à la création
@router.post("/checkout", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    # Corps de la requête, validé automatiquement : contient l'identifiant de l'inscription à payer
    data: PaymentCreate,
    # Service de paiement injecté automatiquement
    service: PaymentService = Depends(get_payment_service),
):
    """Simule le paiement d'une inscription et calcule la commission."""
    try:
        # On convertit l'UUID en chaîne avant de le passer au service, puis on renvoie le paiement créé
        return service.process_payment(str(data.registration_id))
    except ValueError as e:
        # Le service signale une erreur métier (inscription introuvable, déjà payée...) : on la renvoie en 400
        raise HTTPException(status_code=400, detail=str(e))
