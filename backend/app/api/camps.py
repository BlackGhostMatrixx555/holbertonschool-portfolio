"""Routes des camps : espace organisateur et vues publiques."""  # Docstring du module : routes publiques (vitrine) et routes de gestion réservées à l'organisateur.
from uuid import UUID  # Type pour les identifiants de camp passés dans l'URL.

from fastapi import APIRouter, Depends, Query, Response, status  # APIRouter pour grouper les routes, Depends pour l'injection, Query pour les paramètres de filtre, Response et status pour la réponse vide et les codes HTTP.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import CampStatus, User  # Énumération des statuts d'un camp et modèle utilisateur.
from app.schemas.camp import CampInput, CampPublicView, CampView  # Schémas d'entrée (CampInput) et de sortie : version publique (CampPublicView) et version organisateur (CampView).
from app.services import camp_service  # Couche service contenant la logique métier des camps.

router = APIRouter(tags=["Camps"])  # Routeur sans préfixe, regroupé sous "Camps" dans la documentation Swagger.

# ---- Routes publiques (sans authentification) ------------------------------

@router.get("/public/camps", response_model=list[CampPublicView])  # Route GET publique : liste des camps publiés, renvoyée au format public.
def list_public_camps(db: Session = Depends(get_db)):  # Aucune authentification, seule la session est injectée.
    """Liste des camps publiés, pour la page d'accueil."""  # Docstring visible dans Swagger.
    return camp_service.list_public_camps(db)  # Délègue au service, qui ne renvoie que les camps publiés.

@router.get("/camps/{slug}/public", response_model=CampPublicView)  # Route GET publique : détail d'un camp via son slug, au format public.
def get_public_camp(slug: str, db: Session = Depends(get_db)):  # Reçoit le slug et la session, sans authentification.
    """Landing page d'un camp publié, retrouvé par son slug."""  # Docstring visible dans Swagger.
    return camp_service.get_public_camp(db, slug)  # Délègue au service, qui renvoie le camp s'il est publié.

# ---- Routes organisateur (jeton JWT obligatoire) ----------------------------

@router.post("/camps", response_model=CampView, status_code=status.HTTP_201_CREATED)  # Route POST : création d'un camp, réponse 201, format complet organisateur.
def create_camp(  # Crée un camp.
    payload: CampInput,  # Données du camp envoyées par le client, validées par le schéma CampInput.
    current_user: User = Depends(get_current_user),  # Utilisateur connecté (obligatoire), qui devient le propriétaire du camp.
    db: Session = Depends(get_db),  # Session de base de données.
):
    return camp_service.create_camp(db, payload, current_user)  # Délègue la création au service en lui transmettant l'utilisateur comme propriétaire.

@router.get("/camps", response_model=list[CampView])  # Route GET : liste des camps de l'organisateur connecté.
def list_camps(  # Renvoie les camps gérés par l'utilisateur.
    status_filter: CampStatus | None = Query(default=None, alias="status"),  # Filtre optionnel par statut, lu dans le paramètre d'URL "status" (alias) ; sans valeur, pas de filtrage.
    current_user: User = Depends(get_current_user),  # Utilisateur connecté (obligatoire).
    db: Session = Depends(get_db),  # Session de base de données.
):
    return camp_service.list_camps_for(db, current_user, status_filter)  # Délègue au service, qui ne renvoie que les camps de cet utilisateur, éventuellement filtrés.

@router.get("/camps/{camp_id}", response_model=CampView)  # Route GET : détail d'un camp géré, identifié par son UUID.
def get_camp(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Identifiant du camp, utilisateur connecté et session.
    """Détail d'un camp géré (formulaire de modification côté front-end)."""  # Docstring visible dans Swagger.
    return camp_service.get_managed_camp(db, camp_id, current_user)  # Délègue au service, qui vérifie que l'utilisateur gère ce camp avant de le renvoyer.

@router.patch("/camps/{camp_id}", response_model=CampView)  # Route PATCH : modification d'un camp existant.
def update_camp(  # Met à jour un camp.
    camp_id: UUID,  # Identifiant du camp à modifier.
    payload: CampInput,  # Nouvelles données, validées par CampInput.
    current_user: User = Depends(get_current_user),  # Utilisateur connecté (obligatoire).
    db: Session = Depends(get_db),  # Session de base de données.
):
    return camp_service.update_camp(db, camp_id, payload, current_user)  # Délègue au service, qui vérifie les droits avant d'appliquer la modification.

@router.delete("/camps/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)  # Route DELETE : suppression d'un camp, réponse 204 (succès sans contenu).
def delete_camp(camp_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Identifiant du camp, utilisateur connecté et session.
    camp_service.delete_camp(db, camp_id, current_user)  # Délègue la suppression au service, qui vérifie les droits de l'utilisateur.
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # Renvoie explicitement une réponse vide avec le code 204, comme attendu pour une suppression réussie.