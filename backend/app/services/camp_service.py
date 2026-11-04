"""Création, consultation, modification et suppression des camps."""
import re  # Expressions régulières, utilisées pour transformer un nom en slug.
import unicodedata  # Décomposition des caractères accentués, pour les supprimer.
from uuid import UUID  # Type des identifiants de camp.

from sqlalchemy.orm import Session, selectinload  # Session SQLAlchemy et chargement anticipé des relations.

from app.core.exceptions import NotFoundError, ValidationError  # Erreurs métier (404 et 422).
from app.models import Camp, CampModality, CampStatus, User  # Modèles camp, modalité, statut et utilisateur.
from app.schemas.camp import CampInput  # Schéma des données envoyées pour créer ou modifier un camp.
from app.services.permissions import ensure_can_manage_camp, is_super_admin  # Contrôles d'accès.

# Relations chargées en une seule fois avec chaque camp : évite le problème
# "N+1 requêtes" (une requête SQL par camp pour lire ses modalités).
_CAMP_RELATIONS = (  # Relations à charger avec chaque camp.
    selectinload(Camp.modalities),  # Modalités d'éligibilité du camp, chargées en une requête supplémentaire.
    selectinload(Camp.landing_page),  # Landing page du camp, chargée en une requête supplémentaire.
    selectinload(Camp.registrations),  # Inscriptions du camp, chargées en une requête supplémentaire.
)

def slugify(value: str) -> str:  # Transforme un texte en identifiant utilisable dans une URL.
    """'Code Explorers — Été 2026' -> 'code-explorers-ete-2026'."""
    normalized = unicodedata.normalize("NFKD", value)  # sépare lettres et accents
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()  # Supprime les accents et passe en minuscules.
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "camp"  # Remplace les suites de caractères non alphanumériques par un tiret ; "camp" si le résultat est vide.

def _unique_slug(db: Session, name: str) -> str:  # Génère un slug qui n'existe pas encore en base.
    """Ajoute -2, -3... si le slug existe déjà."""
    base_slug = slugify(name)  # Slug de base à partir du nom.
    slug, suffix = base_slug, 2  # Premier candidat et compteur du suffixe.
    while db.query(Camp.id).filter(Camp.slug == slug).first() is not None:  # Tant que le slug est déjà utilisé.
        slug = f"{base_slug}-{suffix}"  # Essaie le slug suivant avec le suffixe.
        suffix += 1  # Incrémente le suffixe pour le prochain essai.
    return slug  # Slug libre.

def create_camp(db: Session, payload: CampInput, organizer: User) -> Camp:  # Crée un camp pour un organisateur.
    data = payload.model_dump(exclude_unset=True)  # Ne garde que les champs réellement envoyés.
    if not data.get("name") or not data.get("start_date") or not data.get("end_date") or not data.get("capacity"):  # Champs obligatoires manquants.
        raise ValidationError("name, dates et capacity sont obligatoires.")

    camp = Camp(  # Crée l'objet camp avec des valeurs par défaut pour les champs optionnels.
        organizer_id=organizer.id,  # L'organisateur est l'utilisateur connecté.
        name=data["name"],
        slug=_unique_slug(db, data["name"]),  # Slug unique généré à partir du nom.
        description=data.get("description"),
        start_date=data["start_date"],
        end_date=data["end_date"],
        city=data.get("city") or "",  # Ville vide si absente.
        age=data.get("age"),
        capacity=data["capacity"],
        status=data.get("status") or CampStatus.DRAFT,  # Brouillon par défaut.
    )
    for modality in data.get("modalities") or []:  # Ajoute chaque modalité envoyée.
        camp.modalities.append(CampModality(**modality))

    db.add(camp)  # Prépare l'insertion du camp et de ses modalités.
    db.commit()  # Enregistre en base.
    db.refresh(camp)  # Recharge le camp depuis la base.
    return camp  # Camp créé.

def list_public_camps(db: Session) -> list[Camp]:  # Liste les camps accessibles au public.
    """Camps publiés, du plus proche au plus lointain."""
    return (
        db.query(Camp)
        .options(*_CAMP_RELATIONS)  # Charge les relations en avance.
        .filter(Camp.status == CampStatus.PUBLISHED)  # Seulement les camps publiés.
        .order_by(Camp.start_date)  # Tri par date de début croissante.
        .all()
    )

def list_camps_for(db: Session, user: User, status: CampStatus | None = None) -> list[Camp]:  # Liste les camps visibles par un utilisateur.
    """Le super admin voit tous les camps ; un organisateur, seulement les siens."""
    query = db.query(Camp).options(*_CAMP_RELATIONS)  # Requête de base avec relations chargées.
    if not is_super_admin(user):  # Un organisateur ne voit que ses camps.
        query = query.filter(Camp.organizer_id == user.id)
    if status is not None:  # Filtre optionnel par statut.
        query = query.filter(Camp.status == status)
    return query.order_by(Camp.start_date).all()  # Tri par date de début croissante.

def get_public_camp(db: Session, slug: str) -> Camp:  # Récupère un camp publié par son slug.
    camp = db.query(Camp).options(*_CAMP_RELATIONS).filter(Camp.slug == slug).first()  # Recherche par slug.
    # Un brouillon répond 404 et non 403 : on ne révèle pas qu'il existe.
    if camp is None or camp.status != CampStatus.PUBLISHED:  # Camp absent ou non publié.
        raise NotFoundError("Camp introuvable.")
    return camp

def get_managed_camp(db: Session, camp_id: UUID, user: User) -> Camp:  # Récupère un camp que l'utilisateur peut gérer.
    """Retourne un camp que l'utilisateur a le droit de gérer."""
    camp = db.query(Camp).options(*_CAMP_RELATIONS).filter(Camp.id == camp_id).first()  # Recherche par identifiant.
    if camp is None:  # Camp inexistant.
        raise NotFoundError("Camp introuvable.")
    ensure_can_manage_camp(camp, user)  # Lève une erreur si l'utilisateur n'a pas le droit.
    return camp

def update_camp(db: Session, camp_id: UUID, payload: CampInput, user: User) -> Camp:  # Modifie partiellement un camp.
    camp = get_managed_camp(db, camp_id, user)  # Camp existant, après contrôle d'accès.
    data = payload.model_dump(exclude_unset=True)  # Seuls les champs envoyés sont modifiés.

    # Mise à jour partielle : on contrôle la cohérence avec les valeurs existantes.
    start_date = data.get("start_date", camp.start_date)  # Nouvelle date de début, ou l'actuelle.
    end_date = data.get("end_date", camp.end_date)  # Nouvelle date de fin, ou l'actuelle.
    if end_date < start_date:  # Dates incohérentes.
        raise ValidationError("end_date doit être supérieure ou égale à start_date")
    if "capacity" in data and data["capacity"] < camp.registrations_count:  # Capacité inférieure au nombre d'inscrits.
        raise ValidationError("La capacité ne peut pas être inférieure au nombre d'inscrits.")

    for key in ("name", "description", "start_date", "end_date", "city", "age", "capacity", "status"):  # Champs simples modifiables.
        if key in data:  # Applique uniquement les champs envoyés.
            setattr(camp, key, data[key])
    if "modalities" in data:  # Remplace toutes les modalités si la liste est envoyée.
        camp.modalities.clear()  # Supprime les anciennes modalités.
        for modality in data["modalities"] or []:  # Ajoute les nouvelles.
            camp.modalities.append(CampModality(**modality))

    db.commit()  # Enregistre les modifications.
    db.refresh(camp)  # Recharge le camp à jour.
    return camp

def delete_camp(db: Session, camp_id: UUID, user: User) -> None:  # Supprime un camp.
    camp = get_managed_camp(db, camp_id, user)  # Vérifie les droits avant suppression.
    db.delete(camp)  # supprime aussi inscriptions, modalités... (cascade)
    db.commit()  # Enregistre la suppression.