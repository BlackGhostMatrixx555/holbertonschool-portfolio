"""
Schémas Pydantic pour les inscriptions.
"""
# uuid : module pour manipuler les identifiants uniques (UUID)
import uuid
# datetime : type pour représenter une date et une heure
from datetime import datetime

# BaseModel : classe de base des schémas Pydantic
# ConfigDict : permet de configurer le comportement d'un schéma
# Field : permet d'ajouter des contraintes de validation sur un champ
from pydantic import BaseModel, ConfigDict, Field

# On importe notre type d'email assoupli (DevEmailStr) en le renommant EmailStr pour l'utiliser comme un EmailStr classique
from app.schemas.types import DevEmailStr as EmailStr


# Schéma des données ENTRANTES : ce que le visiteur envoie en remplissant le formulaire d'inscription
class RegistrationCreate(BaseModel):
    """Données envoyées par un visiteur pour s'inscrire à un camp."""
    # Prénom : obligatoire (...), entre 1 et 100 caractères
    first_name: str = Field(..., min_length=1, max_length=100)
    # Nom de famille : obligatoire, entre 1 et 100 caractères
    last_name: str = Field(..., min_length=1, max_length=100)
    # Email : obligatoire, validé par notre type personnalisé (tolère les TLD réservés comme .test)
    email: EmailStr
    # Commentaire libre : optionnel (peut être du texte ou None), vaut None par défaut
    comment: str | None = None
    # Confirmation de venue : vaut False par défaut si le visiteur ne la coche pas
    confirmed: bool = False


# Schéma des données SORTANTES : ce que l'API renvoie pour afficher une inscription
class RegistrationRead(BaseModel):
    """Inscription telle que renvoyée par l'API (vue admin/organisateur)."""
    # from_attributes=True : permet de construire ce schéma directement depuis un objet SQLAlchemy (modèle de la base)
    model_config = ConfigDict(from_attributes=True)

    # Identifiant unique de l'inscription, généré par le serveur
    id: uuid.UUID
    # Identifiant du camp auquel le visiteur s'est inscrit (lien vers la table des camps)
    camp_id: uuid.UUID
    # Prénom du participant
    first_name: str
    # Nom de famille du participant
    last_name: str
    # Email du participant
    email: EmailStr
    # Commentaire du participant : peut être absent (None)
    comment: str | None
    # Indique si le participant a confirmé sa venue
    confirmed: bool
    # Date et heure de l'inscription, remplies automatiquement par la base de données
    created_at: datetime
