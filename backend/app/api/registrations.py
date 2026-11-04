"""Routes des inscriptions."""  # Docstring du module : routes liées aux inscriptions aux camps.
from uuid import UUID  # Type pour les identifiants passés dans les URL.

from fastapi import APIRouter, Depends, status  # APIRouter pour grouper les routes, Depends pour l'injection, status pour les codes HTTP nommés.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.registration import AttendanceUpdate, RegistrationCreate, RegistrationView  # Schémas d'entrée (création, présence) et de sortie (inscription).
from app.services import registration_service  # Couche service contenant la logique métier des inscriptions.

router = APIRouter(tags=["Inscriptions"])  # Routeur sans préfixe, regroupé sous "Inscriptions" dans la documentation Swagger ; les chemins complets sont indiqués dans chaque route.

@router.post("/camps/{slug}/registrations", response_model=RegistrationView, status_code=status.HTTP_201_CREATED)  # Route POST : inscription à un camp identifié par son slug (version lisible dans l'URL), réponse 201.
def register_for_camp(slug: str, payload: RegistrationCreate, db: Session = Depends(get_db)):  # Reçoit le slug, les données d'inscription et la session. Aucune dépendance d'authentification : route publique.
    """Inscription publique depuis la landing page (sans compte)."""  # Docstring : la route est accessible sans compte utilisateur.
    return registration_service.register(db, slug, payload)  # Délègue l'inscription au service, qui retrouve le camp par son slug.

@router.get("/camps/{camp_id}/registrations", response_model=list[RegistrationView])  # Route GET : liste des inscriptions d'un camp, identifié par son UUID ; réponse sous forme de liste.
def list_camp_registrations(  # Liste les inscrits d'un camp.
    camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db),  # Identifiant du camp, utilisateur connecté (obligatoire) et session.
):
    return registration_service.list_for_camp(db, camp_id, current_user)  # Délègue au service en lui transmettant l'utilisateur, qui vérifie qu'il a le droit de consulter ces inscriptions.

@router.patch("/registrations/{registration_id}/attendance", response_model=RegistrationView)  # Route PATCH : modification de la présence confirmée d'une inscription.
def update_attendance(  # Met à jour la présence d'un inscrit.
    registration_id: UUID, payload: AttendanceUpdate,  # Identifiant de l'inscription et nouvelle valeur de présence.
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),  # Utilisateur connecté (obligatoire) et session.
):
    return registration_service.set_attendance(db, registration_id, payload.confirmed, current_user)  # Délègue au service, qui vérifie les droits de l'utilisateur sur cette inscription.