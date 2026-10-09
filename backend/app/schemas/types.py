"""
Types Pydantic personnalisés.

`EmailStr` par défaut refuse les TLD réservés (`.test`, `.local`, `.example`).
Pour le développement et les tests, on veut pouvoir les utiliser.

Ce type personnalisé assouplit la validation : il garde la vérification
de la syntaxe (partie avant/après le @), mais tolère les TLD réservés.
"""
from typing import Annotated

from pydantic import EmailStr, AfterValidator


def _allow_reserved_tlds(value: str) -> str:
    """Valide l'email en ignorant les restrictions de TLD réservés.

    On utilise `email_validator` directement avec `test_environment=True`,
    ce qui autorise les TLD comme `.test`, `.local`, `.example`.
    """
    from email_validator import validate_email, EmailNotValidError

    try:
        # `test_environment=True` autorise les TLD réservés.
        validate_email(value, test_environment=True, check_deliverability=False)
    except EmailNotValidError as e:
        raise ValueError(str(e))
    return value


# Type EmailStr assoupli pour le dev/test.
DevEmailStr = Annotated[str, AfterValidator(_allow_reserved_tlds)]
