"""
Service métier pour les utilisateurs.

Contient toute la logique liée aux utilisateurs :
- création (avec hachage du mot de passe),
- authentification (email + mot de passe),
- recherche par email ou par ID.
"""
import uuid

from sqlalchemy.orm import Session

from app.models import User, UserStatus
from app.schemas.user import UserCreate
from app.security import hash_password, verify_password


class UserService:
    """Regroupe les opérations métier sur les utilisateurs."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------
    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Récupère un utilisateur par son UUID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email (insensible à la casse)."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def list(self) -> list[User]:
        """Liste tous les utilisateurs, triés par date de création."""
        return self.db.query(User).order_by(User.created_at.desc()).all()

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------
    def create(self, data: UserCreate) -> User:
        """Crée un utilisateur avec mot de passe haché.

        L'utilisateur est créé avec le statut `invited` par défaut.
        """
        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=data.role,
            status=UserStatus.INVITED,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------
    def authenticate(self, email: str, password: str) -> User | None:
        """Vérifie les identifiants et retourne l'utilisateur si valides.

        Retourne None si :
        - l'email n'existe pas,
        - le mot de passe est incorrect,
        - le compte est désactivé.
        """
        user = self.get_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status == UserStatus.DISABLED:
            return None
        return user
