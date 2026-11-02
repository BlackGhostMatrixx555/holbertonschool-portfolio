"""
Connexion à PostgreSQL via SQLAlchemy.

- `engine` gère le pool de connexions ; pool_pre_ping vérifie qu'une
  connexion est toujours vivante avant de la réutiliser.
- `get_db` ouvre une session par requête HTTP et la ferme toujours,
  même en cas d'erreur (bloc finally).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dépendance FastAPI : fournit une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
