"""
Configuration de l'application, lue dans les variables d'environnement.

pydantic-settings lit chaque champ dans l'environnement (ou le fichier .env)
et vérifie son type au démarrage : une configuration invalide empêche l'API
de démarrer, au lieu de provoquer une erreur plus tard en production.
"""
import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- PostgreSQL (données relationnelles : comptes, camps, inscriptions) ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://camporga:camporga@localhost:5432/camporga",
    )

    # --- MongoDB (données documentaires : conversations du chatbot) ---
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "camporga"
    # Durée de conservation des conversations (RGPD : minimisation dans le temps).
    CHAT_RETENTION_DAYS: int = 90

    # --- Sécurité ---
    SECRET_KEY: str = "development-only-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def require_production_secret(self):
        """Refuse de démarrer en production avec la clé de développement."""
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "development-only-change-me":
            raise ValueError("SECRET_KEY must be set to a secure value in production")
        return self


settings = Settings()
