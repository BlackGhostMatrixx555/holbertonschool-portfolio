"""
Connexion à la base de données.

- `engine` : le point d'entrée SQLAlchemy vers PostgreSQL.
- `SessionLocal` : une fabrique de sessions (une session = une transaction).
- `get_db()` : une dépendance FastAPI. Chaque requête HTTP obtient sa propre
  session, qui est automatiquement fermée à la fin (même en cas d'erreur).
- `Base` : la classe dont tous nos modèles (User, Camp, ...) hériteront.
- `pg_enum()` : helper pour créer un type ENUM PostgreSQL en utilisant les
  VALUES Python (minuscules) et non les NAMES (majuscules). À utiliser dans
  tous les modèles pour éviter l'incohérence entre Python et PostgreSQL.
"""
from sqlalchemy import create_engine
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pg_enum(enum_cls, name: str):
    """Crée un type ENUM PostgreSQL en utilisant les VALUES (minuscules)
    et non les NAMES (majuscules).

    Sans `values_callable`, SQLAlchemy utilise `member.name` par défaut
    (ex. `DRAFT`), ce qui crée un enum PostgreSQL avec des valeurs en
    majuscules. Or nos enums Python sont définis en minuscules
    (`DRAFT = "draft"`). Ce helper force SQLAlchemy à utiliser `member.value`,
    alignant Python et PostgreSQL.
    """
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
    )
