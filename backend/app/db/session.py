"""
Connexion à PostgreSQL via SQLAlchemy.

- `engine` gère le pool de connexions ; pool_pre_ping vérifie qu'une
  connexion est toujours vivante avant de la réutiliser.
- `get_db` ouvre une session par requête HTTP et la ferme toujours,
  même en cas d'erreur (bloc finally).
"""  # Docstring du module : rôle de la connexion et de la fonction get_db.
from sqlalchemy import create_engine  # Fonction qui crée le moteur de connexion à la base.
from sqlalchemy.orm import sessionmaker  # Fabrique qui produit des sessions de base de données.

from app.core.config import settings  # Configuration de l'application, contient notamment DATABASE_URL.

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)  # Crée le moteur ; pool_pre_ping teste chaque connexion avant de la réutiliser.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Fabrique de sessions liée au moteur ; autocommit et autoflush désactivés, les commits sont explicites.

def get_db():  # Dépendance FastAPI qui fournit une session à une route.
    """Dépendance FastAPI : fournit une session de base de données."""  # Docstring : usage de la fonction.
    db = SessionLocal()  # Ouvre une nouvelle session pour la requête en cours.
    try:  # Début du bloc protégé.
        yield db  # Fournit la session à la route ; l'exécution reprend ici après la requête.
    finally:  # Exécuté dans tous les cas, succès ou erreur.
        db.close()  # Ferme la session et libère la connexion vers le pool.