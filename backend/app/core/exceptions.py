"""
Erreurs métier de l'application.

Les services ne connaissent pas HTTP : ils lèvent ces exceptions, et
main.py les traduit en réponses HTTP (404, 403, 409, 422).
Cela garde la logique métier indépendante du framework web.
"""  # Docstring du module : rôle des exceptions et lien avec main.py.

class AppError(Exception):  # Classe de base de toutes les erreurs métier, héritée de Exception.
    """Classe de base : porte un message lisible par l'utilisateur."""  # Docstring : rôle de la classe.

    status_code = 400  # Code HTTP par défaut utilisé si une erreur n'en précise pas d'autre (400 : requête invalide).

    def __init__(self, detail: str):  # Constructeur qui reçoit le message d'erreur.
        super().__init__(detail)  # Transmet le message à la classe Exception parente (utile pour l'affichage et les logs).
        self.detail = detail  # Conserve le message dans un attribut pour que main.py puisse le renvoyer au client.

class NotFoundError(AppError):  # Erreur levée quand une ressource est introuvable.
    """La ressource demandée n'existe pas (ou n'est pas visible)."""  # Docstring : cas d'usage.

    status_code = 404  # Code HTTP 404 : ressource non trouvée.

class ForbiddenError(AppError):  # Erreur levée quand l'utilisateur n'a pas le droit d'agir.
    """L'utilisateur est connecté mais n'a pas le droit d'agir."""  # Docstring : cas d'usage.

    status_code = 403  # Code HTTP 403 : accès interdit malgré l'authentification.

class ConflictError(AppError):  # Erreur levée quand l'action contredit l'état actuel.
    """L'action contredit l'état actuel (doublon, camp complet...)."""  # Docstring : exemples de conflits.

    status_code = 409  # Code HTTP 409 : conflit avec l'état de la ressource.

class ValidationError(AppError):  # Erreur levée quand les données sont bien formées mais incohérentes.
    """Les données sont bien formées mais incohérentes."""  # Docstring : cas d'usage.

    status_code = 422  # Code HTTP 422 : entité non traitable (données incohérentes).

class ServiceUnavailableError(AppError):  # Erreur levée quand une dépendance externe ne répond pas.
    """Une dépendance externe (pg_dump, MongoDB...) ne répond pas."""  # Docstring : exemples de dépendances.

    status_code = 503  # Code HTTP 503 : service temporairement indisponible.