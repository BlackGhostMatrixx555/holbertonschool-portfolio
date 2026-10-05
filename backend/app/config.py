"""
Configuration de l'application, lue depuis les variables d'environnement.

Pourquoi un fichier dédié : ça évite d'avoir des `os.getenv(...)` éparpillés
dans le code, et Pydantic valide les valeurs au démarrage (on sait tout de
suite si une variable manque, plutôt que de planter plus tard).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://camporga:camporga@localhost:5432/camporga"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h


settings = Settings()
