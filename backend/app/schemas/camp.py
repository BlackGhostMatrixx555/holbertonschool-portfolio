"""
Schémas Pydantic pour les camps et leurs modalités.
"""
# uuid : module pour manipuler les identifiants uniques (UUID)
import uuid
# date : type pour une date seule (sans heure) / datetime : type pour une date avec heure
from datetime import date, datetime

# BaseModel : classe de base des schémas Pydantic
# ConfigDict : permet de configurer le comportement d'un schéma
# Field : permet d'ajouter des contraintes de validation sur un champ
# model_validator : permet d'écrire une règle de validation portant sur plusieurs champs à la fois
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Énumérations : statut du camp (brouillon, publié...), type de modalité d'éligibilité, thème saisonnier de la landing page
from app.models.enums import CampStatus, ModalityType, SeasonTheme


# Schéma ENTRANT : une modalité (condition d'éligibilité) à créer en même temps que le camp
class ModalityCreate(BaseModel):
    # Type de la modalité, selon l'énumération ModalityType
    type: ModalityType
    # Texte affiché pour décrire la modalité : obligatoire, entre 1 et 255 caractères
    label: str = Field(..., min_length=1, max_length=255)


# Schéma SORTANT : une modalité telle que renvoyée par l'API
class ModalityRead(BaseModel):
    # from_attributes=True : permet de construire ce schéma directement depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
    # Identifiant unique de la modalité, généré par le serveur
    id: uuid.UUID
    # Type de la modalité
    type: ModalityType
    # Texte descriptif de la modalité
    label: str


# Schéma ENTRANT : les données envoyées par l'organisateur pour créer un camp
class CampCreate(BaseModel):
    # Nom du camp : obligatoire (...), entre 1 et 150 caractères
    name: str = Field(..., min_length=1, max_length=150)
    # Description du camp : optionnelle, vaut None par défaut
    description: str | None = None
    # Date de début : obligatoire
    start_date: date
    # Date de fin : obligatoire
    end_date: date
    # Ville du camp : optionnelle, 100 caractères maximum
    city: str | None = Field(None, max_length=100)
    # Âge (cible ou minimum selon votre règle métier) : optionnel, compris entre 0 et 120 (ge = supérieur ou égal, le = inférieur ou égal)
    age: int | None = Field(None, ge=0, le=120)
    # Nombre de places : vaut 0 par défaut, ne peut pas être négatif
    capacity: int = Field(0, ge=0)
    # Statut du camp : vaut "brouillon" par défaut, le camp n'est donc pas visible tant que l'organisateur ne le publie pas
    status: CampStatus = CampStatus.DRAFT
    # Liste des modalités à créer avec le camp : liste vide par défaut (default_factory évite de partager la même liste entre les objets)
    modalities: list[ModalityCreate] = Field(default_factory=list)

    # Règle de validation exécutée APRÈS la validation de chaque champ individuel
    @model_validator(mode="after")
    def check_dates(self):
        # Si la date de fin est avant la date de début, les données sont incohérentes
        if self.end_date < self.start_date:
            # On lève une erreur, qui sera renvoyée au client (erreur 422)
            raise ValueError("end_date doit être supérieure ou égale à start_date")
        # Si tout est bon, on renvoie l'objet validé
        return self


# Schéma ENTRANT : les données envoyées pour modifier un camp (mise à jour partielle)
class CampUpdate(BaseModel):
    # Tous les champs sont optionnels (None) : seuls ceux fournis par le client seront modifiés
    name: str | None = Field(None, min_length=1, max_length=150)
    # Nouvelle description
    description: str | None = None
    # Nouvelle date de début
    start_date: date | None = None
    # Nouvelle date de fin
    end_date: date | None = None
    # Nouvelle ville
    city: str | None = Field(None, max_length=100)
    # Nouvel âge, avec les mêmes bornes qu'à la création
    age: int | None = Field(None, ge=0, le=120)
    # Nouvelle capacité, jamais négative
    capacity: int | None = Field(None, ge=0)
    # Nouveau statut du camp
    status: CampStatus | None = None

    # Règle de validation exécutée après la validation des champs
    @model_validator(mode="after")
    def check_dates(self):
        # On ne compare les dates que si le client a fourni LES DEUX (sinon on ne peut pas comparer)
        if self.start_date is not None and self.end_date is not None:
            # Même règle qu'à la création : la fin ne peut pas précéder le début
            if self.end_date < self.start_date:
                # Erreur renvoyée au client
                raise ValueError("end_date doit être supérieure ou égale à start_date")
        # On renvoie l'objet validé
        return self


# Schéma SORTANT : la landing page associée à un camp
class LandingPageRead(BaseModel):
    # Permet la construction depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
    # Identifiant unique de la landing page
    id: uuid.UUID
    # Thème visuel saisonnier de la page
    season_theme: SeasonTheme
    # Titre principal affiché en haut de la page (peut être vide)
    hero_title: str | None
    # Texte d'accroche sous le titre (peut être vide)
    hero_description: str | None
    # Date de publication : None tant que la page n'est pas publiée
    published_at: datetime | None


# Schéma SORTANT : un camp complet, destiné à l'organisateur et à l'admin
class CampRead(BaseModel):
    # Permet la construction depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
    # Identifiant unique du camp
    id: uuid.UUID
    # Identifiant de l'organisateur propriétaire du camp
    organizer_id: uuid.UUID
    # Nom du camp
    name: str
    # Version du nom utilisable dans une URL (ex. "summer-camp-2026"), sert à l'adresse de la landing page
    slug: str
    # Description du camp
    description: str | None
    # Date de début
    start_date: date
    # Date de fin
    end_date: date
    # Ville
    city: str | None
    # Âge
    age: int | None
    # Nombre de places
    capacity: int
    # Statut du camp
    status: CampStatus
    # Date de création du camp, renseignée par le serveur
    created_at: datetime
    # Liste des modalités du camp (vide par défaut)
    modalities: list[ModalityRead] = Field(default_factory=list)


# Schéma SORTANT : la version PUBLIQUE d'un camp, affichée sur la landing page
class CampPublicRead(BaseModel):
    # Permet la construction depuis un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
    # Identifiant unique du camp
    id: uuid.UUID
    # Nom du camp
    name: str
    # Slug utilisé dans l'URL publique
    slug: str
    # Description du camp
    description: str | None
    # Date de début
    start_date: date
    # Date de fin
    end_date: date
    # Ville
    city: str | None
    # Âge
    age: int | None
    # Nombre de places total (ajouté pour que le frontend puisse afficher "X/Y places")
    capacity: int
    # Statut du camp
    status: CampStatus
    # Modalités d'éligibilité à afficher
    modalities: list[ModalityRead] = Field(default_factory=list)
    # Landing page associée (None si elle n'existe pas encore)
    landing_page: LandingPageRead | None = None
    # Nombre d'inscrits (ajouté pour le compteur), 0 par défaut
    registration_count: int = 0
