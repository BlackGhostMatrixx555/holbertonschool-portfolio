"""Schémas de la landing page publique d'un camp."""  # Docstring du module : schémas de la landing page publique d'un camp.
from datetime import datetime  # Type des dates et heures, utilisé pour la date de publication.
from uuid import UUID  # Type des identifiants (landing page, camp).

from pydantic import BaseModel, ConfigDict, Field  # Classes de base Pydantic, configuration et contraintes de champs.

from app.models import SeasonTheme  # Énumération des thèmes saisonniers de la landing page.

class LandingPageUpdate(BaseModel):  # Données pour mettre à jour la landing page d'un camp.
    season_theme: SeasonTheme  # Thème saisonnier appliqué à la page.
    hero_title: str = Field(min_length=1, max_length=200)  # Titre principal obligatoire, entre 1 et 200 caractères.
    hero_description: str | None = Field(default=None, max_length=2000)  # Description facultative, 2000 caractères maximum.
    # True = publier le camp ; False = le repasser en brouillon.  # Explication du rôle du champ publish.
    publish: bool = False  # Publication désactivée par défaut, la page reste en brouillon.

class LandingPageView(BaseModel):  # Représentation d'une landing page renvoyée par l'API.
    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant de la landing page.
    camp_id: UUID  # Identifiant du camp auquel elle appartient.
    season_theme: SeasonTheme  # Thème saisonnier actuel.
    hero_title: str  # Titre principal affiché.
    hero_description: str | None  # Description affichée, pouvant être vide.
    published_at: datetime | None  # Date de publication, vide si la page est en brouillon.