import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://camporga:camporga@localhost:5432/camporga",
    )
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
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "development-only-change-me":
            raise ValueError("SECRET_KEY must be set to a secure value in production")
        return self


settings = Settings()