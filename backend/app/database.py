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
# create_engine : fonction qui crée la connexion principale vers la base de données
from sqlalchemy import create_engine
# On importe Enum de SQLAlchemy sous le nom SAEnum pour ne pas le confondre avec l'Enum de Python
from sqlalchemy import Enum as SAEnum
# sessionmaker : fabrique de sessions / declarative_base : crée la classe de base des modèles
from sqlalchemy.orm import sessionmaker, declarative_base

# settings : la configuration de l'application (variables d'environnement, dont l'URL de la base)
from app.config import settings

# On crée l'engine : le point d'entrée vers PostgreSQL, à partir de l'URL de connexion
# pool_pre_ping=True : teste la connexion avant de l'utiliser, pour éviter les connexions mortes
engine = create_engine(settings.database_url, pool_pre_ping=True)
# On crée la fabrique de sessions, liée à l'engine
# autocommit=False : on valide les changements nous-mêmes avec commit()
# autoflush=False : SQLAlchemy n'envoie pas les changements automatiquement avant chaque requête
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# On crée la classe de base dont tous les modèles (User, Camp, etc.) vont hériter
Base = declarative_base()


# Dépendance FastAPI : fournit une session de base de données à chaque requête
def get_db():
    # On ouvre une nouvelle session pour cette requête
    db = SessionLocal()
    # On utilise try/finally pour garantir la fermeture de la session
    try:
        # yield : on "prête" la session à la route, puis on reprend la main quand elle a fini
        yield db
    # Ce bloc s'exécute toujours, même si une erreur survient dans la route
    finally:
        # On ferme la session pour libérer la connexion à la base
        db.close()


# Helper : fonction utilitaire qui crée un type ENUM PostgreSQL à partir d'un Enum Python
def pg_enum(enum_cls, name: str):
    """Crée un type ENUM PostgreSQL en utilisant les VALUES (minuscules)
    et non les NAMES (majuscules).

    Sans `values_callable`, SQLAlchemy utilise `member.name` par défaut
    (ex. `DRAFT`), ce qui crée un enum PostgreSQL avec des valeurs en
    majuscules. Or nos enums Python sont définis en minuscules
    (`DRAFT = "draft"`). Ce helper force SQLAlchemy à utiliser `member.value`,
    alignant Python et PostgreSQL.
    """
    # On retourne un type Enum SQLAlchemy configuré pour PostgreSQL
    return SAEnum(
        # La classe Enum Python à convertir (ex. UserRole)
        enum_cls,
        # Le nom du type ENUM qui sera créé dans PostgreSQL
        name=name,
        # Fonction qui dit à SQLAlchemy d'utiliser les valeurs (m.value) plutôt que les noms (m.name)
        values_callable=lambda e: [m.value for m in e],
    )
