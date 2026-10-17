import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Updated credentials to match docker-compose setup
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://camporga:camporga@localhost:5432/camporga",
    )

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()