"""
Configuration de l'application, lue dans les variables d'environnement.

pydantic-settings lit chaque champ dans l'environnement (ou le fichier .env)
et vérifie son type au démarrage : une configuration invalide empêche l'API
de démarrer, au lieu de provoquer une erreur plus tard en production.
"""  # Docstring du module : rôle de la configuration et intérêt de la validation au démarrage.
import os  # Module standard pour lire les variables d'environnement.

from pydantic import model_validator  # Décorateur pour valider l'ensemble des champs après leur chargement.
from pydantic_settings import BaseSettings, SettingsConfigDict  # Classe de base qui lit l'environnement, et sa configuration.

class Settings(BaseSettings):  # Classe regroupant toute la configuration ; chaque attribut est lu depuis l'environnement.
    # --- PostgreSQL (données relationnelles : comptes, camps, inscriptions) ---
    DATABASE_URL: str = os.getenv(  # URL de connexion PostgreSQL ; os.getenv lit d'abord la variable d'environnement.
        "DATABASE_URL",  # Nom de la variable d'environnement lue.
        "postgresql://camporga:camporga@localhost:5432/camporga",  # Valeur par défaut pour le développement local.
    )

    # --- MongoDB (données documentaires : conversations du chatbot) ---
    MONGO_URL: str = "mongodb://localhost:27017"  # Adresse de connexion MongoDB, par défaut en local.
    MONGO_DB_NAME: str = "camporga"  # Nom de la base MongoDB utilisée.
    # Durée de conservation des conversations (RGPD : minimisation dans le temps).
    CHAT_RETENTION_DAYS: int = 90  # Nombre de jours avant suppression automatique des conversations.

    # --- Sauvegardes et vérification ---
    BACKUP_DIR: str = "/app/backups"  # Dossier où sont stockées les sauvegardes.
    VERIFICATION_CODE_TTL_MINUTES: int = 5  # Durée de validité d'un code de vérification, en minutes.
    VERIFICATION_MAX_ATTEMPTS: int = 5  # Nombre de tentatives autorisées avant blocage du code.

    # --- Sécurité ---
    SECRET_KEY: str = "development-only-change-me"  # Clé de signature des jetons JWT ; valeur de développement à remplacer.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Durée de validité d'un jeton de session, en minutes.
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]  # Origines autorisées à appeler l'API depuis un navigateur.
    ENVIRONMENT: str = "development"  # Environnement d'exécution : development, production...

    @property  # Permet d'utiliser settings.is_development comme un attribut, sans parenthèses.
    def is_development(self) -> bool:  # Indique si l'application tourne en développement.
        return self.ENVIRONMENT.lower() == "development"  # Compare l'environnement en minuscules, pour tolérer "Development" ou "DEVELOPMENT".

    model_config = SettingsConfigDict(  # Configuration du comportement de pydantic-settings.
        case_sensitive=True,  # Les noms de variables d'environnement sont sensibles à la casse.
        env_file=".env",  # Fichier dont les valeurs sont lues si elles ne sont pas dans l'environnement.
        extra="ignore",  # Ignore les variables inconnues au lieu de lever une erreur.
    )

    @model_validator(mode="after")  # Exécute cette validation après le chargement de tous les champs.
    def require_production_secret(self):  # Vérifie la cohérence de la configuration de production.
        """Refuse de démarrer en production avec la clé de développement."""  # Docstring : rôle de la vérification.
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "development-only-change-me":  # En production avec la clé par défaut...
            raise ValueError("SECRET_KEY must be set to a secure value in production")  # ...on empêche le démarrage de l'application.
        return self  # Retourne l'instance validée si tout est correct.

settings = Settings()  # Crée l'instance unique de configuration, importée ensuite par le reste de l'application.