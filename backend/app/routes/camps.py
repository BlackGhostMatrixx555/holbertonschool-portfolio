"""
Routes HTTP pour les camps.
"""
# uuid : pour typer les identifiants de camp et d'inscription
import uuid
# APIRouter : regroupe les routes ; Depends : injection de dépendances ; HTTPException : erreurs HTTP ; Query : paramètres de l'URL ; status : codes HTTP nommés
from fastapi import APIRouter, Depends, HTTPException, Query, status
# Session : session SQLAlchemy, c'est-à-dire une transaction avec la base
from sqlalchemy.orm import Session

# get_db : fournit une session de base de données par requête
from app.database import get_db
# get_current_user : renvoie l'utilisateur connecté à partir de son JWT
from app.dependencies import get_current_user
# Modèles et énumérations utilisés directement dans les routes
from app.models import Camp, CampStatus, Registration, User, UserRole
# Schémas de validation des camps
from app.schemas.camp import CampCreate, CampPublicRead, CampRead, CampUpdate
# Schémas de validation des inscriptions
from app.schemas.registration import RegistrationCreate, RegistrationRead
# Services métier : logique des camps et des inscriptions
from app.services.camp_service import CampService
from app.services.registration_service import RegistrationService

# Groupe de routes préfixé par /camps, rangé sous le tag "camps" dans la doc Swagger
router = APIRouter(prefix="/camps", tags=["camps"])

# Fabrique du service camps : FastAPI lui passe la session de base de données
def get_camp_service(db: Session = Depends(get_db)) -> CampService:
    # On renvoie un service branché sur cette session
    return CampService(db)

# Fabrique du service inscriptions : même principe
def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    # On renvoie un service branché sur cette session
    return RegistrationService(db)

# ---------------------------------------------------------------------------
# CRUD Camps
# ---------------------------------------------------------------------------
# Route POST /camps : crée un camp, réservée aux utilisateurs connectés (201 à la création)
@router.post("", response_model=CampRead, status_code=status.HTTP_201_CREATED)
def create_camp(
    # Corps de la requête, validé automatiquement par le schéma CampCreate
    data: CampCreate,
    # Service des camps injecté automatiquement
    service: CampService = Depends(get_camp_service),
    # Utilisateur connecté : la requête est refusée sans JWT valide
    current_user: User = Depends(get_current_user),
):
    # Le camp est rattaché à l'utilisateur connecté, qui devient son organisateur
    return service.create(data, organizer_id=current_user.id)

# Route GET /camps : liste les camps, avec filtres optionnels sur le statut et l'organisateur
@router.get("", response_model=list[CampRead])
def list_camps(
    # Filtre optionnel sur le statut, passé dans l'URL sous le nom "status"
    status_filter: CampStatus | None = Query(None, alias="status"),
    # Filtre optionnel sur l'organisateur
    organizer_id: uuid.UUID | None = Query(None),
    # Service des camps injecté automatiquement
    service: CampService = Depends(get_camp_service),
):
    # Route publique : seuls les filtres sont appliqués, aucun contrôle d'identité
    return service.list(status=status_filter, organizer_id=organizer_id)

# Route PATCH /camps/{camp_id} : modifie partiellement un camp
@router.patch("/{camp_id}", response_model=CampRead)
def update_camp(
    # Identifiant du camp, extrait de l'URL
    camp_id: uuid.UUID,
    # Champs à modifier, tous optionnels dans CampUpdate
    data: CampUpdate,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    # On récupère le camp ciblé
    camp = service.get_by_id(camp_id)
    # Si le camp n'existe pas, on renvoie une erreur 404
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    # Rôles autorisés à modifier n'importe quel camp, en plus de l'organisateur
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    # Contrôle d'accès : l'utilisateur doit être l'organisateur du camp ou avoir un rôle autorisé
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier ce camp.")
    # Mise à jour effectuée par le service
    return service.update(camp, data)

# Route DELETE /camps/{camp_id} : supprime un camp (204 : succès sans contenu)
@router.delete("/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camp(
    # Identifiant du camp à supprimer
    camp_id: uuid.UUID,
    service: CampService = Depends(get_camp_service),
    current_user: User = Depends(get_current_user),
):
    # On récupère le camp ciblé
    camp = service.get_by_id(camp_id)
    # Si le camp n'existe pas, on renvoie une erreur 404
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    # Rôles autorisés à supprimer n'importe quel camp
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    # Contrôle d'accès identique à la modification
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer ce camp.")
    # Suppression effectuée par le service
    service.delete(camp)
    # Pas de contenu renvoyé, conformément au code 204
    return None

# ---------------------------------------------------------------------------
# Landing Page (Vue publique avec compteur)
# ---------------------------------------------------------------------------
# Route GET /camps/{slug}/public : données publiques d'un camp pour sa landing page
@router.get("/{slug}/public", response_model=CampPublicRead)
def get_public_camp(
    # Slug du camp (version lisible du nom, utilisée dans l'URL)
    slug: str,
    service: CampService = Depends(get_camp_service),
    reg_service: RegistrationService = Depends(get_registration_service),
):
    # On cherche le camp par son slug
    camp = service.get_by_slug(slug)
    # Si aucun camp ne correspond, erreur 404
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")

    # On construit la réponse manuellement pour y injecter le compteur
    # model_validate transforme le modèle SQLAlchemy en schéma, model_dump le convertit en dictionnaire
    response_data = CampPublicRead.model_validate(camp).model_dump()
    # On ajoute le nombre d'inscrits, calculé à la volée
    response_data["registration_count"] = reg_service.count_for_camp(camp.id)
    return response_data

# ---------------------------------------------------------------------------
# Inscriptions (Visiteurs & Organisateurs)
# ---------------------------------------------------------------------------
# Route POST /camps/{camp_id}/registrations : inscription publique à un camp (201 à la création)
@router.post("/{camp_id}/registrations", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_to_camp(
    # Identifiant du camp visé
    camp_id: uuid.UUID,
    # Données du participant : nom, prénom, email, commentaire, confirmation
    data: RegistrationCreate,
    reg_service: RegistrationService = Depends(get_registration_service),
):
    """Inscription publique (aucune authentification requise)."""
    try:
        # Le service crée l'inscription après ses propres contrôles (camp complet, doublon...)
        return reg_service.create(camp_id, data)
    except ValueError as e:
        # Erreur métier remontée par le service, renvoyée en 400
        raise HTTPException(status_code=400, detail=str(e))

# Route GET /camps/{camp_id}/registrations : liste des inscrits, réservée aux responsables
@router.get("/{camp_id}/registrations", response_model=list[RegistrationRead])
def list_registrations(
    camp_id: uuid.UUID,
    # Session directe, utilisée ici pour vérifier l'existence et le propriétaire du camp
    db: Session = Depends(get_db),
    reg_service: RegistrationService = Depends(get_registration_service),
    current_user: User = Depends(get_current_user),
):
    """Liste des inscrits. Réservé aux organisateurs du camp, directeurs et super admin."""
    # Requête directe pour récupérer le camp
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    # Camp inexistant : erreur 404
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")

    # Rôles autorisés à voir les inscrits
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    # Contrôle d'accès : organisateur du camp ou rôle autorisé
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Vous n'avez pas le droit de voir les inscrits de ce camp.")

    # Liste des inscrits renvoyée par le service
    return reg_service.list_for_camp(camp_id)

# Route DELETE /camps/{camp_id}/registrations/{registration_id} : supprime une inscription (204)
@router.delete("/{camp_id}/registrations/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registration(
    camp_id: uuid.UUID,
    # Identifiant de l'inscription à supprimer
    registration_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une inscription (Organisateur du camp / Directeur / Super Admin)."""
    # On récupère le camp
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    # Camp inexistant : erreur 404
    if not camp:
        raise HTTPException(status_code=404, detail="Camp introuvable.")

    # Rôles autorisés à supprimer une inscription
    allowed_roles = [UserRole.SUPER_ADMIN, UserRole.DIRECTEUR_CAMPUS, UserRole.DIRECTEUR_TECHNIQUE]
    # Contrôle d'accès identique aux autres routes sensibles
    if camp.organizer_id != current_user.id and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Action non autorisée.")

    # On cherche l'inscription, en vérifiant qu'elle appartient bien à ce camp
    # Le double filtre empêche de supprimer une inscription d'un autre camp via l'URL
    reg = db.query(Registration).filter(Registration.id == registration_id, Registration.camp_id == camp_id).first()
    # Inscription introuvable : erreur 404
    if not reg:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")

    # Suppression directe en base, puis validation de la transaction
    db.delete(reg)
    db.commit()
    # Pas de contenu renvoyé, conformément au code 204
    return None
