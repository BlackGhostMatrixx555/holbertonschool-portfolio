"""Règles d'autorisation communes à plusieurs services."""
from app.core.exceptions import ForbiddenError  # Erreur métier levée quand l'utilisateur n'a pas le droit d'agir (traduite en 403).
from app.models import Camp, User, UserRole  # Modèles utilisés : le camp, l'utilisateur et l'énumération des rôles.

def is_super_admin(user: User) -> bool:  # Indique si l'utilisateur est super administrateur.
    return user.role == UserRole.SUPER_ADMIN  # Vrai uniquement si le rôle correspond au super admin.

def ensure_can_manage_camp(camp: Camp, user: User) -> None:  # Vérifie qu'un utilisateur peut gérer un camp donné.
    """
    Un camp ne peut être géré que par son organisateur ou par le super admin.
    Utilisé pour la modification, la suppression, les inscriptions et les messages.
    """
    if camp.organizer_id != user.id and not is_super_admin(user):  # Ni l'organisateur du camp, ni super admin : accès refusé.
        raise ForbiddenError("Permissions insuffisantes.")  # Interrompt l'action avec une erreur 403.
    # Sinon, la fonction ne fait rien : l'action peut continuer.