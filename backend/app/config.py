"""
Configuration de l'application, lue depuis les variables d'environnement.

Pourquoi un fichier dédié : ça évite d'avoir des `os.getenv(...)` éparpillés
dans le code, et Pydantic valide les valeurs au démarrage (on sait tout de
suite si une variable manque, plutôt que de planter plus tard).
"""
# BaseSettings : classe Pydantic qui lit automatiquement les variables d'environnement
# SettingsConfigDict : permet de configurer le comportement de la classe (fichier .env, etc.)
from pydantic_settings import BaseSettings, SettingsConfigDict


# On définit la classe qui regroupe tous les paramètres de l'application
class Settings(BaseSettings):
    # env_file=".env" : on lit aussi les variables depuis le fichier .env
    # extra="ignore" : si le .env contient des variables non déclarées ici, on les ignore (pas d'erreur)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # URL de connexion à PostgreSQL (utilisateur:mot_de_passe@hôte:port/nom_de_la_base)
    # La valeur après le = est la valeur par défaut, utilisée si DATABASE_URL n'est pas définie
    database_url: str = "postgresql://camporga:camporga@localhost:5432/camporga"
    # Clé secrète qui sert à signer les tokens JWT (à remplacer par une vraie clé en production)
    secret_key: str = "change-me-in-production"
    # Algorithme de signature des tokens JWT (HS256 = HMAC avec SHA-256)
    algorithm: str = "HS256"
    # Durée de vie d'un token d'accès en minutes : 60 * 24 = 1440 minutes = 24 heures
    access_token_expire_minutes: int = 60 * 24  # 24h


# On crée une instance unique de Settings, importée partout dans l'application
# C'est ici que les variables sont lues et validées au démarrage
settings = Settings()
