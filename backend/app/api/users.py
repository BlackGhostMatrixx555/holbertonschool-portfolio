"""Comptes : profil personnel (/users/me) et administration (super admin)."""  # Docstring du module : deux familles de routes.
from uuid import UUID  # Type pour les identifiants utilisateurs passés dans les URL.

from fastapi import APIRouter, Depends, Response, status  # APIRouter pour grouper les routes, Depends pour l'injection, Response et status pour les réponses HTTP.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user, require_super_admin  # Dépendances d'authentification et de contrôle de rôle.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.user import ProfileUpdate, UserCreate, UserRoleUpdate, UserStatusUpdate, UserView  # Schémas de validation des données entrantes et de la réponse.
from app.services import user_service  # Couche service contenant la logique métier.

router = APIRouter(prefix="/users", tags=["Utilisateurs"])  # Routeur préfixé par /users, regroupé sous "Utilisateurs" dans la documentation Swagger.

# ---- Son propre compte (tout utilisateur connecté) ------------------------------
# Déclarées AVANT /{user_id} : sinon "me" serait lu comme un identifiant.

@router.patch("/me", response_model=UserView)  # Route PATCH /users/me : modification partielle du profil ; la réponse suit le schéma UserView.
def update_my_profile(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Reçoit les données à modifier, l'utilisateur connecté et la session.
    return user_service.update_profile(db, current_user, payload)  # Délègue la mise à jour au service ; seul le compte courant est modifié.

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)  # Route DELETE /users/me : suppression de son propre compte, réponse sans contenu (204).
def delete_my_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Reçoit l'utilisateur connecté et la session.
    user_service.delete_own_account(db, current_user)  # Délègue la suppression au service.
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # Renvoie explicitement une réponse vide avec le code 204.

# ---- Administration (super admin) ---------------------------------------------

@router.get("", response_model=list[UserView])  # Route GET /users : liste de tous les utilisateurs, sous forme de liste de UserView.
def list_users(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Le "_" indique que l'utilisateur super admin n'est vérifié que pour son autorisation, sans être utilisé.
    return user_service.list_users(db)  # Délègue la récupération de la liste au service.

@router.post("", response_model=UserView, status_code=status.HTTP_201_CREATED)  # Route POST /users : création d'un utilisateur, réponse 201 (créé).
def create_user(payload: UserCreate, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Reçoit les données du nouvel utilisateur ; seul le super admin peut appeler cette route.
    return user_service.create_user(db, payload)  # Délègue la création au service.

@router.patch("/{user_id}/role", response_model=UserView)  # Route PATCH /users/{user_id}/role : changement du rôle d'un utilisateur.
def update_user_role(  # Modifie le rôle d'un utilisateur donné.
    user_id: UUID, payload: UserRoleUpdate,  # Identifiant de l'utilisateur ciblé (validé comme UUID) et nouveau rôle.
    current_user: User = Depends(require_super_admin), db: Session = Depends(get_db),  # Super admin courant (transmis au service pour éviter, par exemple, qu'il se retire ses propres droits) et session.
):
    return user_service.update_role(db, user_id, payload.role, current_user)  # Délègue le changement au service avec le super admin courant pour les contrôles métier.

@router.patch("/{user_id}/status", response_model=UserView)  # Route PATCH /users/{user_id}/status : activation ou désactivation d'un compte.
def update_user_status(  # Modifie le statut d'un utilisateur donné.
    user_id: UUID, payload: UserStatusUpdate,  # Identifiant ciblé et nouveau statut.
    current_user: User = Depends(require_super_admin), db: Session = Depends(get_db),  # Super admin courant et session.
):
    return user_service.update_status(db, user_id, payload.status, current_user)  # Délègue le changement au service avec le super admin courant pour les contrôles métier.

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)  # Route DELETE /users/{user_id} : suppression d'un utilisateur par le super admin, réponse 204.
def delete_user(user_id: UUID, _: User = Depends(require_super_admin), db: Session = Depends(get_db)):  # Identifiant ciblé ; le super admin est vérifié sans être utilisé directement.
    user_service.delete_user(db, user_id)  # Délègue la suppression au service.
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # Renvoie une réponse vide avec le code 204.