import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampOrga"
    API_V1_STR: str = "/api/v1"
    
    # Updated credentials to match docker-compose setup
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://camporga:camporga@localhost:5432/camporga"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()