"""Création, consultation, modification et suppression des camps."""
import re
import unicodedata
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Camp, CampModality, CampStatus, User
from app.schemas.camp import CampInput
from app.services.permissions import ensure_can_manage_camp, is_super_admin

# Relations chargées en une seule fois avec chaque camp : évite le problème
# "N+1 requêtes" (une requête SQL par camp pour lire ses modalités).
_CAMP_RELATIONS = (
    selectinload(Camp.modalities),
    selectinload(Camp.landing_page),
    selectinload(Camp.registrations),
)


def slugify(value: str) -> str:
    """'Code Explorers — Été 2026' -> 'code-explorers-ete-2026'."""
    normalized = unicodedata.normalize("NFKD", value)  # sépare lettres et accents
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "camp"


def _unique_slug(db: Session, name: str) -> str:
    """Ajoute -2, -3... si le slug existe déjà."""
    base_slug = slugify(name)
    slug, suffix = base_slug, 2
    while db.query(Camp.id).filter(Camp.slug == slug).first() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def create_camp(db: Session, payload: CampInput, organizer: User) -> Camp:
    data = payload.model_dump(exclude_unset=True)
    if not data.get("name") or not data.get("start_date") or not data.get("end_date") or not data.get("capacity"):
        raise ValidationError("name, dates et capacity sont obligatoires.")

    age = data.get("age")
    camp = Camp(
        organizer_id=organizer.id,
        name=data["name"],
        slug=_unique_slug(db, data["name"]),
        description=data.get("description"),
        start_date=data["start_date"],
        end_date=data["end_date"],
        city=data.get("city") or "",
        min_age=data.get("min_age", age if age is not None else 0),
        max_age=data.get("max_age", age if age is not None else 0),
        capacity=data["capacity"],
        status=data.get("status") or CampStatus.DRAFT,
    )
    for modality in data.get("modalities") or []:
        camp.modalities.append(CampModality(**modality))

    db.add(camp)
    db.commit()
    db.refresh(camp)
    return camp


def list_public_camps(db: Session) -> list[Camp]:
    """Camps publiés, du plus proche au plus lointain."""
    return (
        db.query(Camp)
        .options(*_CAMP_RELATIONS)
        .filter(Camp.status == CampStatus.PUBLISHED)
        .order_by(Camp.start_date)
        .all()
    )


def list_camps_for(db: Session, user: User, status: CampStatus | None = None) -> list[Camp]:
    """Le super admin voit tous les camps ; un organisateur, seulement les siens."""
    query = db.query(Camp).options(*_CAMP_RELATIONS)
    if not is_super_admin(user):
        query = query.filter(Camp.organizer_id == user.id)
    if status is not None:
        query = query.filter(Camp.status == status)
    return query.order_by(Camp.start_date).all()


def get_public_camp(db: Session, slug: str) -> Camp:
    camp = db.query(Camp).options(*_CAMP_RELATIONS).filter(Camp.slug == slug).first()
    # Un brouillon répond 404 et non 403 : on ne révèle pas qu'il existe.
    if camp is None or camp.status != CampStatus.PUBLISHED:
        raise NotFoundError("Camp introuvable.")
    return camp


def get_managed_camp(db: Session, camp_id: UUID, user: User) -> Camp:
    """Retourne un camp que l'utilisateur a le droit de gérer."""
    camp = db.query(Camp).options(*_CAMP_RELATIONS).filter(Camp.id == camp_id).first()
    if camp is None:
        raise NotFoundError("Camp introuvable.")
    ensure_can_manage_camp(camp, user)
    return camp


def update_camp(db: Session, camp_id: UUID, payload: CampInput, user: User) -> Camp:
    camp = get_managed_camp(db, camp_id, user)
    data = payload.model_dump(exclude_unset=True)

    # Mise à jour partielle : on contrôle la cohérence avec les valeurs existantes.
    start_date = data.get("start_date", camp.start_date)
    end_date = data.get("end_date", camp.end_date)
    if end_date < start_date:
        raise ValidationError("end_date doit être supérieure ou égale à start_date")
    if "capacity" in data and data["capacity"] < camp.registrations_count:
        raise ValidationError("La capacité ne peut pas être inférieure au nombre d'inscrits.")

    for key in ("name", "description", "start_date", "end_date", "city", "capacity", "status"):
        if key in data:
            setattr(camp, key, data[key])
    if "age" in data:
        camp.min_age = camp.max_age = data["age"]
    if "min_age" in data:
        camp.min_age = data["min_age"]
    if "max_age" in data:
        camp.max_age = data["max_age"]
    if camp.min_age > camp.max_age:
        raise ValidationError("min_age doit être inférieur ou égal à max_age")
    if "modalities" in data:
        camp.modalities.clear()
        for modality in data["modalities"] or []:
            camp.modalities.append(CampModality(**modality))

    db.commit()
    db.refresh(camp)
    return camp


def delete_camp(db: Session, camp_id: UUID, user: User) -> None:
    camp = get_managed_camp(db, camp_id, user)
    db.delete(camp)  # supprime aussi inscriptions, modalités... (cascade)
    db.commit()
