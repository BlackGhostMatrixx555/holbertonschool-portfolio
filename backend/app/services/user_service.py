"""Gestion des comptes : connexion, inscription, profil, administration, suppression."""
from datetime import timedelta  # Permet de manipuler des durées (ici la validité du jeton).
from uuid import UUID  # Type des identifiants des utilisateurs.

from sqlalchemy.orm import Session  # Session SQLAlchemy, qui sert à interroger et modifier la base.

from app.core.config import settings  # Configuration globale (durée de validité des jetons, etc.).
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError  # Erreurs métier : conflit, interdit, introuvable.
from app.core.security import create_access_token, create_two_factor_token, hash_password, verify_password  # Fonctions de sécurité : jetons et mots de passe.
from app.models import Backup, Camp, User, UserRole, UserStatus  # Modèles de données utilisés dans ce service.
from app.schemas.auth import RegisterRequest  # Schéma de données de l'inscription publique.
from app.schemas.user import ProfileUpdate, UserCreate  # Schémas de mise à jour du profil et de création d'utilisateur.

class InvalidCredentialsError(Exception):  # Exception levée quand l'email ou le mot de passe est faux.
    """Identifiants refusés (traduit en 401 par la route de connexion)."""

class PendingAccountError(Exception):  # Exception levée quand le compte n'est pas encore validé.
    """Mot de passe correct, mais compte pas encore validé (traduit en 403)."""

def _token_response(user: User) -> dict:  # Fonction privée : construit la réponse contenant le jeton de session.
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convertit la durée de validité de minutes en secondes.
    token = create_access_token(subject=user.id, expires_delta=timedelta(seconds=expires_in))  # Crée un jeton d'accès signé pour cet utilisateur.
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}  # Format standard d'une réponse d'authentification.

def authenticate(db: Session, email: str, password: str) -> dict:  # Étape 1 de la connexion.
    """
    Étape 1 de la connexion : vérifie l'email et le mot de passe.

    - Même message que l'email existe ou non : on ne révèle pas quels comptes
      existent (énumération de comptes).
    - Si la 2FA est activée, on ne délivre PAS de jeton de session : seulement
      un jeton temporaire pour l'étape 2 (le code à 6 chiffres).
    """
    user = db.query(User).filter(User.email == email.strip().lower()).first()  # Cherche l'utilisateur, email normalisé (sans espaces, en minuscules).
    if user is None or not verify_password(password, user.password_hash) or user.status == UserStatus.DISABLED:  # Compte absent, mot de passe faux ou compte désactivé.
        raise InvalidCredentialsError("Email ou mot de passe incorrect.")  # Message volontairement générique.
    if user.status == UserStatus.INACTIVE:  # Le mot de passe est correct mais le compte n'est pas validé.
        # Le mot de passe est juste : on peut expliquer pourquoi l'accès est refusé.
        raise PendingAccountError("Votre compte est en attente de validation par le super admin.")

    if user.is_2fa_enabled:  # La double authentification est activée pour ce compte.
        return {"requires_2fa": True, "temp_token": create_two_factor_token(user.id)}  # Renvoie seulement un jeton temporaire.
    return _token_response(user)  # Pas de 2FA : connexion complète immédiate.

def complete_two_factor_login(user: User) -> dict:  # Étape 2 de la connexion.
    """Étape 2 de la connexion : le code TOTP a été vérifié par le service 2FA."""
    return _token_response(user)  # Le code est valide : on délivre le jeton de session.

def register(db: Session, payload: RegisterRequest) -> User:  # Inscription publique d'un organisateur.
    """
    Inscription publique d'un organisateur (apport de tete-work).

    Le compte est créé INACTIF avec le rôle SEM : le cahier des charges confie
    la gestion des accès au super admin, qui doit l'activer. Sans cette étape,
    n'importe qui pourrait créer des camps publics sur la plateforme.
    """
    email = payload.email.lower()  # Normalise l'email en minuscules.
    if db.query(User.id).filter(User.email == email).first() is not None:  # Vérifie qu'aucun compte n'utilise déjà cet email.
        raise ConflictError("Cette adresse email est déjà utilisée.")  # Refuse l'inscription si l'email existe.
    user = User(  # Crée l'objet utilisateur (encore pas enregistré en base).
        email=email,
        password_hash=hash_password(payload.password),  # Stocke le hash du mot de passe.
        first_name=payload.first_name.strip(),  # Supprime les espaces superflus.
        last_name=payload.last_name.strip(),
        phone_number=payload.phone_number,
        role=UserRole.SEM,  # Rôle d'organisateur.
        status=UserStatus.INACTIVE,  # En attente de validation par le super admin.
    )
    db.add(user)  # Prépare l'insertion.
    db.commit()  # Enregistre en base.
    db.refresh(user)  # Recharge l'objet depuis la base (pour récupérer id, dates générées, etc.).
    return user

def list_users(db: Session) -> list[User]:  # Liste tous les utilisateurs.
    return db.query(User).order_by(User.created_at.desc()).all()  # Du plus récent au plus ancien.

def create_user(db: Session, payload: UserCreate) -> User:  # Création d'un utilisateur par un administrateur.
    email = payload.email.lower()  # Normalise l'email.
    if db.query(User.id).filter(User.email == email).first() is not None:  # Email déjà pris.
        raise ConflictError("Cette adresse email est déjà utilisée.")

    user = User(  # Nouvel utilisateur.
        email=email,
        password_hash=hash_password(payload.password),  # jamais le mot de passe en clair
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,  # Rôle choisi par l'administrateur.
        status=UserStatus.ACTIVE,  # Compte directement actif, contrairement à l'inscription publique.
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:  # Met à jour le profil de l'utilisateur connecté.
    for key, value in payload.model_dump(exclude_unset=True).items():  # Ne parcourt que les champs réellement envoyés par le client.
        setattr(user, key, value)  # Applique chaque valeur à l'objet utilisateur.
    db.commit()
    db.refresh(user)
    return user

def _get_user(db: Session, user_id: UUID) -> User:  # Fonction privée : récupère un utilisateur par son identifiant.
    user = db.get(User, user_id)  # Recherche par clé primaire ; None si absent.
    if user is None:
        raise NotFoundError("Utilisateur introuvable.")
    return user

def update_role(db: Session, user_id: UUID, role: UserRole, current_user: User) -> User:  # Change le rôle d'un utilisateur.
    user = _get_user(db, user_id)
    # Garde-fou : un super admin qui se rétrograderait laisserait la plateforme
    # sans personne pour gérer les comptes.
    if user.id == current_user.id and role != UserRole.SUPER_ADMIN:  # Tentative de se retirer soi-même le rôle super admin.
        raise ConflictError("Vous ne pouvez pas modifier votre propre rôle.")
    user.role = role
    db.commit()
    db.refresh(user)
    return user

def update_status(db: Session, user_id: UUID, new_status: UserStatus, current_user: User) -> User:  # Change le statut d'un utilisateur (actif, inactif, désactivé).
    user = _get_user(db, user_id)
    # Garde-fou : le super admin ne doit pas pouvoir se bloquer lui-même.
    if user.id == current_user.id and new_status != UserStatus.ACTIVE:  # Tentative de se désactiver soi-même.
        raise ConflictError("Vous ne pouvez pas désactiver votre propre compte.")
    user.status = new_status
    db.commit()
    db.refresh(user)
    return user

def _delete(db: Session, user: User) -> None:  # Fonction privée : suppression commune aux deux cas.
    """
    Supprime un compte s'il n'a plus de données rattachées.

    On refuse (409) plutôt que de supprimer en cascade : supprimer un
    organisateur effacerait sinon ses camps ET les inscriptions des familles.
    """
    if db.query(Camp.id).filter(Camp.organizer_id == user.id).first() is not None:  # Le compte organise encore au moins un camp.
        raise ConflictError("Ce compte gère encore des camps : supprimez-les ou transférez-les d'abord.")
    if db.query(Backup.id).filter(Backup.triggered_by == user.id).first() is not None:  # Le compte a lancé au moins une sauvegarde.
        raise ConflictError("Ce compte a réalisé des sauvegardes : il doit être conservé pour la traçabilité.")
    db.delete(user)  # Marque l'utilisateur pour suppression.
    db.commit()  # Exécute la suppression.

def delete_own_account(db: Session, user: User) -> None:  # Un utilisateur supprime son propre compte.
    """Suppression de son propre compte (apport de tete-work)."""
    if user.role == UserRole.SUPER_ADMIN:  # Le super admin ne peut pas supprimer son compte.
        raise ForbiddenError("Le compte super admin ne peut pas être supprimé.")
    _delete(db, user)

def delete_user(db: Session, user_id: UUID) -> None:  # Un administrateur supprime le compte d'un autre utilisateur.
    """Suppression d'un compte par le super admin."""
    user = _get_user(db, user_id)
    if user.role == UserRole.SUPER_ADMIN:  # Aucun compte super admin ne peut être supprimé par ce biais.
        raise ForbiddenError("Un compte super admin ne peut pas être supprimé.")
    _delete(db, user)