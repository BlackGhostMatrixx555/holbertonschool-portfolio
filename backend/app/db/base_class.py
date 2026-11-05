"""Base déclarative SQLAlchemy partagée par tous les modèles."""
from sqlalchemy.orm import declarative_base

# Classe de base commune à tous les modèles : chaque classe qui en hérite
# devient une table. Alembic lit Base.metadata pour générer les migrations.
Base = declarative_base()
