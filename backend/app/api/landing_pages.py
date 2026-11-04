"""Route de création / publication de la landing page d'un camp."""  # Docstring du module : création ou publication de la page vitrine d'un camp.
from uuid import UUID  # Type pour l'identifiant du camp passé dans l'URL.

from fastapi import APIRouter, Depends  # APIRouter pour grouper les routes, Depends pour l'injection de dépendances.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.landing_page import LandingPageUpdate, LandingPageView  # Schéma d'entrée (données de la page) et schéma de sortie.
from app.services import landing_page_service  # Couche service contenant la logique métier de la landing page.

router = APIRouter(tags=["Landing pages"])  # Routeur sans préfixe, regroupé sous "Landing pages" dans la documentation Swagger.

@router.put("/camps/{camp_id}/landing-page", response_model=LandingPageView)  # Route PUT sur la landing page du camp identifié par son UUID ; la réponse suit le schéma LandingPageView.
def update_landing_page(  # Crée ou remplace la landing page d'un camp.
    camp_id: UUID, payload: LandingPageUpdate,  # Identifiant du camp (validé comme UUID) et contenu complet de la page.
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),  # Utilisateur connecté (obligatoire) et session.
):
    # PUT : la landing page est remplacée entièrement (opération idempotente).  # Commentaire : envoyer deux fois la même requête produit le même résultat, sans doublon.
    return landing_page_service.upsert_landing_page(db, camp_id, payload, current_user)  # Délègue au service, qui crée la page si elle n'existe pas, sinon la remplace, après vérification des droits de l'utilisateur.