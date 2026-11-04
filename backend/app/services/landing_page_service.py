"""Création et publication de la landing page d'un camp."""
from datetime import datetime, timezone  # datetime pour horodater la publication ; timezone.utc pour qu'elle soit en UTC.
from uuid import UUID  # Type des identifiants des camps.

from sqlalchemy.orm import Session  # Session SQLAlchemy pour interroger et modifier la base.

from app.models import CampStatus, LandingPage, User  # Modèles utilisés : landing page, statut du camp, utilisateur.
from app.schemas.landing_page import LandingPageUpdate  # Schéma des données envoyées pour mettre à jour la page.
from app.services.camp_service import get_managed_camp  # Récupère le camp en vérifiant que l'utilisateur peut le gérer.

def upsert_landing_page(db: Session, camp_id: UUID, payload: LandingPageUpdate, user: User) -> LandingPage:  # Crée ou met à jour la landing page.
    """
    Crée la landing page si elle n'existe pas, sinon la met à jour ("upsert").
    Publier la page publie aussi le camp, ce qui ouvre les inscriptions.
    """
    camp = get_managed_camp(db, camp_id, user)  # Récupère le camp et vérifie les droits de l'utilisateur.

    landing_page = camp.landing_page  # Page existante liée au camp, ou None si elle n'a jamais été créée.
    if landing_page is None:  # Première fois : on crée la page.
        landing_page = LandingPage(camp_id=camp.id)  # Lie la page au camp.
        db.add(landing_page)  # Prépare l'insertion en base.

    landing_page.season_theme = payload.season_theme  # Met à jour le thème de saison.
    landing_page.hero_title = payload.hero_title  # Met à jour le titre principal.
    landing_page.hero_description = payload.hero_description  # Met à jour la description.

    if payload.publish:  # L'utilisateur demande la publication.
        # On garde la date de première publication si la page était déjà en ligne.
        landing_page.published_at = landing_page.published_at or datetime.now(timezone.utc)  # Ne remplace pas la date si elle existe déjà.
        camp.status = CampStatus.PUBLISHED  # Le camp devient visible et ouvert aux inscriptions.
    else:  # Demande de repasser en brouillon.
        landing_page.published_at = None  # Retire la date de publication.
        camp.status = CampStatus.DRAFT  # Le camp n'est plus visible ni ouvert aux inscriptions.

    db.commit()  # Enregistre les modifications en base.
    db.refresh(landing_page)  # Recharge la page depuis la base pour récupérer les valeurs à jour.
    return landing_page  # Renvoie la page créée ou mise à jour.