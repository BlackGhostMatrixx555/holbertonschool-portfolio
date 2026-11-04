"""Inscriptions publiques aux camps et suivi des présences."""
from uuid import UUID  # Type des identifiants (UUID) des camps et des inscriptions.

from sqlalchemy import func  # Fonctions SQL (ici count et lower) utilisables dans les requêtes.
from sqlalchemy.orm import Session  # Session SQLAlchemy pour interroger et modifier la base.

from app.core.exceptions import ConflictError, NotFoundError  # Erreurs métier : conflit (doublon, complet) et introuvable.
from app.models import Camp, CampStatus, Registration, User  # Modèles de données utilisés.
from app.schemas.registration import RegistrationCreate  # Schéma des données envoyées pour une inscription.
from app.services.camp_service import get_managed_camp  # Vérifie que l'utilisateur a le droit de gérer le camp.

def register(db: Session, slug: str, payload: RegistrationCreate) -> Registration:  # Inscription publique à un camp.
    """
    Inscrit un visiteur à un camp publié.

    SELECT ... FOR UPDATE verrouille la ligne du camp pendant la transaction :
    si deux personnes s'inscrivent à la dernière place au même moment,
    la seconde attend la fin de la première et voit le camp complet.
    """
    camp = db.query(Camp).filter(Camp.slug == slug).with_for_update().first()  # Cherche le camp par son slug et verrouille sa ligne jusqu'à la fin de la transaction.
    if camp is None or camp.status != CampStatus.PUBLISHED:  # Camp inexistant ou non publié : on ne le révèle pas à un visiteur.
        raise NotFoundError("Camp introuvable.")

    email = payload.email.lower()  # Normalise l'email en minuscules pour comparer sans tenir compte de la casse.
    already_registered = db.query(Registration.id).filter(  # Cherche une inscription existante avec le même email pour ce camp.
        Registration.camp_id == camp.id,
        func.lower(Registration.email) == email,  # Comparaison insensible à la casse côté base de données.
    ).first()
    if already_registered:  # Un doublon a été trouvé.
        raise ConflictError("Une inscription existe déjà pour cet email.")

    count = db.query(func.count(Registration.id)).filter(Registration.camp_id == camp.id).scalar()  # Compte les inscriptions déjà enregistrées pour ce camp.
    if count >= camp.capacity:  # Plus de place disponible.
        raise ConflictError("Ce camp a atteint sa capacité maximale.")

    registration = Registration(  # Crée l'objet inscription avec les données nettoyées (espaces supprimés aux extrémités).
        camp_id=camp.id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        comment=payload.comment,
    )
    db.add(registration)  # Prépare l'insertion en base.
    db.commit()  # libère aussi le verrou
    db.refresh(registration)  # Recharge l'objet depuis la base pour récupérer les valeurs générées (identifiant, date...).
    return registration

def list_for_camp(db: Session, camp_id: UUID, user: User) -> list[Registration]:  # Liste les inscriptions d'un camp, réservée aux gestionnaires.
    get_managed_camp(db, camp_id, user)  # contrôle d'accès : lève une erreur si l'utilisateur ne gère pas ce camp.
    return (
        db.query(Registration)
        .filter(Registration.camp_id == camp_id)  # Uniquement les inscriptions de ce camp.
        .order_by(Registration.created_at.desc())  # Les plus récentes d'abord.
        .all()
    )

def set_attendance(db: Session, registration_id: UUID, confirmed: bool, user: User) -> Registration:  # Marque une inscription comme présente ou non.
    registration = db.get(Registration, registration_id)  # Recherche l'inscription par son identifiant.
    if registration is None:  # Inscription inexistante.
        raise NotFoundError("Inscription introuvable.")
    get_managed_camp(db, registration.camp_id, user)  # Vérifie que l'utilisateur gère le camp de cette inscription.
    registration.confirmed = confirmed  # Met à jour le statut de présence.
    db.commit()
    db.refresh(registration)
    return registration