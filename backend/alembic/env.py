import os  # Module standard pour manipuler les chemins de fichiers et les variables d'environnement.
import sys  # Module standard pour accéder au chemin de recherche Python (sys.path).
from logging.config import fileConfig  # Fonction qui configure les logs à partir du fichier alembic.ini.
from sqlalchemy import engine_from_config, pool  # engine_from_config crée un moteur à partir d'une configuration, pool fournit les stratégies de connexion.
from alembic import context  # Objet contextuel d'Alembic, qui donne accès à la configuration et aux migrations en cours.

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # Ajoute le dossier parent de env.py (la racine du projet) au début du chemin de recherche, pour que l'import du package "app" fonctionne.

from app.core.config import settings  # Configuration de l'application, notamment l'URL de la base de données.
from app.db.base_class import Base  # Classe de base déclarative de SQLAlchemy, dont héritent tous les modèles.
import app.models  # Importe les modèles pour qu'ils soient enregistrés dans Base.metadata ; sans cet import, Alembic ne verrait pas les tables.

config = context.config  # Récupère la configuration Alembic (le contenu de alembic.ini).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)  # Injecte l'URL de la base issue des paramètres de l'application, plutôt que celle écrite en dur dans alembic.ini.

if config.config_file_name is not None:  # Vérifie qu'un fichier de configuration a bien été chargé.
    fileConfig(config.config_file_name)  # Applique la configuration de logs définie dans ce fichier.

target_metadata = Base.metadata  # Décrit le schéma attendu : Alembic compare cette description à la base réelle pour générer les migrations automatiques.

def run_migrations_offline() -> None:  # Mode hors ligne : génère le SQL des migrations sans se connecter à la base.
    url = config.get_main_option("sqlalchemy.url")  # Lit l'URL de la base depuis la configuration.
    context.configure(  # Configure le contexte Alembic pour le mode hors ligne.
        url=url,  # URL utilisée pour adapter le dialecte SQL, sans ouvrir de connexion.
        target_metadata=target_metadata,  # Schéma cible pour l'autogénération.
        literal_binds=True,  # Écrit les valeurs directement dans le SQL généré, au lieu de paramètres liés.
        dialect_opts={"paramstyle": "named"},  # Style des paramètres de requête dans le SQL produit.
    )
    with context.begin_transaction():  # Ouvre une transaction pour l'ensemble des migrations.
        context.run_migrations()  # Exécute les migrations, ou les écrit en SQL dans ce mode.

def run_migrations_online() -> None:  # Mode en ligne : applique les migrations directement sur la base.
    connectable = engine_from_config(  # Crée un moteur SQLAlchemy à partir de la section de configuration d'Alembic.
        config.get_section(config.config_ini_section, {}),  # Récupère la section [alembic] du fichier de configuration, ou un dictionnaire vide si elle est absente.
        prefix="sqlalchemy.",  # Ne prend en compte que les clés commençant par "sqlalchemy.".
        poolclass=pool.NullPool,  # Désactive le pool de connexions : chaque connexion est fermée dès la fin, ce qui est adapté à un script de migration ponctuel.
    )
    with connectable.connect() as connection:  # Ouvre une connexion à la base, fermée automatiquement à la sortie du bloc.
        context.configure(  # Configure le contexte Alembic avec cette connexion active.
            connection=connection, target_metadata=target_metadata  # Connexion utilisée pour appliquer les migrations, et schéma cible pour la comparaison.
        )
        with context.begin_transaction():  # Ouvre une transaction pour appliquer les migrations.
            context.run_migrations()  # Exécute les migrations sur la base.

if context.is_offline_mode():  # Détermine le mode demandé lors de l'appel à Alembic (par exemple avec l'option --sql).
    run_migrations_offline()  # Mode hors ligne : génère le SQL sans toucher à la base.
else:  # Sinon, le mode est en ligne.
    run_migrations_online()  # Applique les migrations directement sur la base.