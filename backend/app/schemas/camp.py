"""Schémas des camps, de leurs modalités et de leur landing page."""  # Docstring du module.
from datetime import date, datetime  # Types pour les dates de camp et l'horodatage de publication.
from uuid import UUID  # Type des identifiants (camp, organisateur).

from pydantic import BaseModel, ConfigDict, Field, model_validator  # Outils Pydantic : modèle de base, configuration, contraintes de champs et validation globale.

from app.models import CampStatus, ModalityType, SeasonTheme  # Énumérations du statut du camp, du type de modalité et du thème saisonnier.

class ModalityInput(BaseModel):  # Modalité saisie lors de la création ou de la mise à jour d'un camp.
    type: ModalityType  # Type de modalité.
    label: str = Field(min_length=1, max_length=200)  # Libellé affiché, entre 1 et 200 caractères.

class CampInput(BaseModel):  # Données d'un camp pour la création (POST) et la mise à jour (PATCH).
    """
    Données d'un camp, utilisées en création (POST) et en mise à jour (PATCH).

    Tous les champs sont optionnels pour permettre une mise à jour partielle ;
    le service vérifie que les champs obligatoires sont présents à la création.
    """  # Explication : tous les champs sont optionnels, la vérification des obligations est faite par le service.

    model_config = ConfigDict(extra="ignore")  # Ignore silencieusement les champs inconnus envoyés par le client.

    name: str | None = Field(default=None, min_length=1, max_length=200)  # Nom du camp, entre 1 et 200 caractères.
    description: str | None = Field(default=None, max_length=5000)  # Description longue, jusqu'à 5000 caractères.
    start_date: date | None = None  # Date de début du camp.
    end_date: date | None = None  # Date de fin du camp.
    city: str | None = Field(default=None, max_length=100)  # Ville où se déroule le camp.
    # Âge minimum requis ("à partir de X ans") ; null = tous âges.  # Explication de la valeur nulle.
    age: int | None = Field(default=None, ge=0, le=99)  # Âge minimum, entre 0 et 99 ans.
    capacity: int | None = Field(default=None, ge=1, le=10000)  # Nombre maximal de places, entre 1 et 10000.
    status: CampStatus | None = None  # Statut du camp (brouillon, publié, archivé).
    modalities: list[ModalityInput] | None = Field(default=None, max_length=20)  # Liste des modalités, au maximum 20.

    @model_validator(mode="after")  # Validation exécutée après la construction de l'objet, sur l'ensemble des champs.
    def check_consistency(self):  # Vérifie la cohérence entre plusieurs champs.
        """Règles qui portent sur plusieurs champs à la fois."""  # Docstring : règles multi-champs.
        if self.start_date and self.end_date and self.end_date < self.start_date:  # Si les deux dates sont fournies et que la fin précède le début.
            raise ValueError("end_date doit être supérieure ou égale à start_date")  # Rejette la donnée avec un message d'erreur.
        return self  # Retourne l'instance validée.

class ModalityView(BaseModel):  # Modalité telle que renvoyée par l'API.
    model_config = ConfigDict(from_attributes=True)  # Autorise la construction à partir d'objets SQLAlchemy.

    type: ModalityType  # Type de modalité.
    label: str  # Libellé affiché.

class LandingPageSummary(BaseModel):  # Résumé de la landing page d'un camp.
    model_config = ConfigDict(from_attributes=True)  # Construction à partir d'objets SQLAlchemy.

    season_theme: SeasonTheme  # Thème saisonnier visuel.
    hero_title: str  # Titre principal de la page.
    hero_description: str | None  # Description d'accroche, facultative.
    published_at: datetime | None  # Date de publication, absente si non publiée.

class CampPublicView(BaseModel):  # Vue publique : ce qu'un visiteur anonyme peut voir d'un camp publié.
    """Ce qu'un visiteur anonyme peut voir d'un camp publié."""  # Docstring : périmètre de la vue publique.

    model_config = ConfigDict(from_attributes=True)  # Construction à partir d'objets SQLAlchemy.

    id: UUID  # Identifiant du camp.
    name: str  # Nom du camp.
    slug: str  # Identifiant lisible utilisé dans l'URL.
    description: str | None  # Description, facultative.
    start_date: date  # Date de début.
    end_date: date  # Date de fin.
    city: str  # Ville du camp.
    age: int | None  # Âge minimum requis, null si tous âges.
    status: CampStatus  # Statut du camp.
    remaining_places: int  # Nombre de places encore disponibles.
    modalities: list[ModalityView]  # Modalités du camp.
    landing_page: LandingPageSummary | None  # Résumé de la landing page, absent si aucune.

class CampView(CampPublicView):  # Vue organisateur, qui hérite de la vue publique.
    """Vue organisateur : ajoute les champs internes."""  # Docstring : champs internes ajoutés.

    organizer_id: UUID  # Identifiant de l'organisateur propriétaire du camp.
    capacity: int  # Capacité totale du camp.
    registrations_count: int  # Nombre d'inscriptions enregistrées.