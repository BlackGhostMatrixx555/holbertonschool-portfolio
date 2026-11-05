"""
Erreurs métier de l'application.

Les services ne connaissent pas HTTP : ils lèvent ces exceptions, et
main.py les traduit en réponses HTTP (404, 403, 409, 422).
Cela garde la logique métier indépendante du framework web.
"""


class AppError(Exception):
    """Classe de base : porte un message lisible par l'utilisateur."""

    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    """La ressource demandée n'existe pas (ou n'est pas visible)."""

    status_code = 404


class ForbiddenError(AppError):
    """L'utilisateur est connecté mais n'a pas le droit d'agir."""

    status_code = 403


class ConflictError(AppError):
    """L'action contredit l'état actuel (doublon, camp complet...)."""

    status_code = 409


class ValidationError(AppError):
    """Les données sont bien formées mais incohérentes."""

    status_code = 422


class ServiceUnavailableError(AppError):
    """Une dépendance externe (pg_dump, MongoDB...) ne répond pas."""

    status_code = 503
