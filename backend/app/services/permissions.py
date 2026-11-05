"""Règles d'autorisation communes à plusieurs services."""
from app.core.exceptions import ForbiddenError
from app.models import Camp, User, UserRole


def is_super_admin(user: User) -> bool:
    return user.role == UserRole.SUPER_ADMIN


def ensure_can_manage_camp(camp: Camp, user: User) -> None:
    """
    Un camp ne peut être géré que par son organisateur ou par le super admin.
    Utilisé pour la modification, la suppression, les inscriptions et les messages.
    """
    if camp.organizer_id != user.id and not is_super_admin(user):
        raise ForbiddenError("Permissions insuffisantes.")
