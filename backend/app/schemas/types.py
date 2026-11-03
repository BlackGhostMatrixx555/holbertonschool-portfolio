"""
Types Pydantic personnalisés.

`EmailStr` par défaut refuse les TLD réservés (`.test`, `.local`, `.example`).
Pour le développement et les tests, on veut pouvoir les utiliser.

Ce type personnalisé assouplit la validation : il garde la vérification
de la syntaxe (partie avant/après le @), mais tolère les TLD réservés.
"""
# Annotated : permet d'attacher des informations supplémentaires (ici un validateur) à un type
from typing import Annotated

# EmailStr : type d'email standard de Pydantic (importé ici mais non utilisé directement dans ce fichier)
# AfterValidator : permet d'exécuter une fonction de validation APRÈS la validation de base du type
from pydantic import EmailStr, AfterValidator


# Fonction de validation personnalisée (le _ au début indique qu'elle est privée à ce module)
# Elle reçoit l'email sous forme de texte et renvoie l'email validé
def _allow_reserved_tlds(value: str) -> str:
    """Valide l'email en ignorant les restrictions de TLD réservés.

    On utilise `email_validator` directement avec `test_environment=True`,
    ce qui autorise les TLD comme `.test`, `.local`, `.example`.
    """
    # On importe la bibliothèque email_validator ici, au moment où la fonction est appelée
    # validate_email : fonction qui vérifie la syntaxe / EmailNotValidError : l'erreur levée si l'email est invalide
    from email_validator import validate_email, EmailNotValidError

    # On tente la validation, en capturant l'erreur si l'email est invalide
    try:
        # `test_environment=True` autorise les TLD réservés.
        # check_deliverability=False : on ne vérifie pas que le domaine existe réellement (pas de requête DNS)
        validate_email(value, test_environment=True, check_deliverability=False)
    # Si l'email n'est pas valide, la bibliothèque lève EmailNotValidError
    except EmailNotValidError as e:
        # On convertit en ValueError : c'est le type d'erreur que Pydantic sait transformer en message d'erreur 422
        raise ValueError(str(e))
    # Si tout est bon, on renvoie l'email tel quel (inchangé)
    return value


# Type EmailStr assoupli pour le dev/test.
# Annotated[str, ...] : c'est un str normal, auquel on ajoute notre validateur personnalisé
# À chaque fois qu'un champ est typé DevEmailStr, Pydantic exécute _allow_reserved_tlds dessus
DevEmailStr = Annotated[str, AfterValidator(_allow_reserved_tlds)]
