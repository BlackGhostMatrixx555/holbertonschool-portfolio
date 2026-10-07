"""
Service métier pour les camps.

La couche service contient la logique métier (génération de slug, création
des modalités, etc.). Les routers ne font que :
  - valider l'entrée (via Pydantic),
  - vérifier les droits,
  - appeler le service,
  - renvoyer la réponse.

Avantage : la logique est testable sans passer par HTTP.
"""
import re
import unicodedata
import uuid

from sqlalchemy.orm import Session

from app.models import Camp, CampModality
from app.schemas.camp import CampCreate, CampUpdate


def slugify(name: str) -> str:
    """Transforme un nom de camp en slug lisible pour l'URL.

    Exemple : "Code Explorers — Été 2025" -> "code-explorers-ete-2025"
    """
    # 1. Décompose les caractères accentués (é -> e + accent) et retire les accents.
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    # 2. Minuscules, remplace tout ce qui n'est pas alphanumérique par un tiret.
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "camp"


class CampService:
    """Regroupe les opérations métier sur les camps."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Slug
    # ------------------------------------------------------------------
    def _generate_unique_slug(self, name: str) -> str:
        """Génère un slug unique. Ajoute -2, -3, ... en cas de collision."""
        base = slugify(name)
        slug = base
        counter = 2
        while self.db.query(Camp).filter(Camp.slug == slug).first() is not None:
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------
    def create(self, data: CampCreate, organizer_id: uuid.UUID) -> Camp:
        """Crée un camp et ses modalités associées."""
        camp = Camp(
            organizer_id=organizer_id,
            name=data.name,
            slug=self._generate_unique_slug(data.name),
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            city=data.city,
            age=data.age,
            capacity=data.capacity,
            status=data.status,
        )
        for modality in data.modalities:
            camp.modalities.append(
                CampModality(type=modality.type, label=modality.label)
            )

        self.db.add(camp)
        self.db.commit()
        self.db.refresh(camp)
        return camp

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------
    def list(
        self,
        status: str | None = None,
        organizer_id: uuid.UUID | None = None,
    ) -> list[Camp]:
        """Liste les camps, avec filtres optionnels."""
        query = self.db.query(Camp)
        if status is not None:
            query = query.filter(Camp.status == status)
        if organizer_id is not None:
            query = query.filter(Camp.organizer_id == organizer_id)
        return query.order_by(Camp.created_at.desc()).all()

    def get_by_slug(self, slug: str) -> Camp | None:
        """Récupère un camp par son slug (utilisé par la route publique)."""
        return self.db.query(Camp).filter(Camp.slug == slug).first()

    def get_by_id(self, camp_id: uuid.UUID) -> Camp | None:
        """Récupère un camp par son UUID (utilisé par PATCH et DELETE)."""
        return self.db.query(Camp).filter(Camp.id == camp_id).first()

    # ------------------------------------------------------------------
    # Mise à jour
    # ------------------------------------------------------------------
    def update(self, camp: Camp, data: CampUpdate) -> Camp:
        """Met à jour les champs fournis (les autres restent inchangés)."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(camp, field, value)
        self.db.commit()
        self.db.refresh(camp)
        return camp

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------
    def delete(self, camp: Camp) -> None:
        """Supprime un camp. Les modalités, la landing page et les inscriptions
        liées sont supprimées en cascade grâce à `cascade="all, delete-orphan"`.
        """
        self.db.delete(camp)
        self.db.commit()
