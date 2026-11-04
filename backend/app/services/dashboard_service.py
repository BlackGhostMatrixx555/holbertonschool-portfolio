"""Indicateurs du tableau de bord organisateur."""
from sqlalchemy import case, func  # case : expression conditionnelle SQL (CASE WHEN) ; func : fonctions SQL d'agrégation (count).
from sqlalchemy.orm import Session  # Session SQLAlchemy pour interroger la base.

from app.models import Camp, CampStatus, Registration, User  # Modèles utilisés : camps, statuts de camp, inscriptions, utilisateurs.
from app.services.permissions import is_super_admin  # Permet de savoir si l'utilisateur voit tous les camps.

def summary(db: Session, user: User) -> dict:  # Construit les indicateurs du tableau de bord.
    """
    Compte les camps par statut en UNE requête SQL (agrégation avec CASE),
    puis récupère les 10 dernières inscriptions grâce à une jointure.
    """
    camps_filter = [] if is_super_admin(user) else [Camp.organizer_id == user.id]  # Super admin : aucun filtre (tous les camps) ; sinon uniquement les camps de l'organisateur.

    total, draft, published, archived = db.query(  # Une seule requête qui calcule les quatre compteurs à la fois.
        func.count(Camp.id),  # Nombre total de camps.
        func.count(case((Camp.status == CampStatus.DRAFT, 1))),  # Compte uniquement les camps en brouillon (CASE renvoie 1, sinon NULL, que count ignore).
        func.count(case((Camp.status == CampStatus.PUBLISHED, 1))),  # Compte uniquement les camps publiés.
        func.count(case((Camp.status == CampStatus.ARCHIVED, 1))),  # Compte uniquement les camps archivés.
    ).filter(*camps_filter).one()  # Applique le filtre de droits et retourne exactement une ligne.

    registrations = db.query(Registration).join(Camp, Registration.camp_id == Camp.id).filter(*camps_filter)  # Inscriptions jointes à leur camp, avec le même filtre de droits.

    return {
        "camps": {"total": total, "draft": draft, "published": published, "archived": archived},  # Compteurs des camps par statut.
        "registrations": {"total": registrations.count()},  # Nombre total d'inscriptions visibles par l'utilisateur.
        "recent_registrations": registrations.order_by(Registration.created_at.desc()).limit(10).all(),  # Les 10 inscriptions les plus récentes.
    }