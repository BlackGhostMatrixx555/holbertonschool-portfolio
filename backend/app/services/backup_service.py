"""
Sauvegardes de la base, réservées au super admin.  # Docstring du module : description générale.

Fusion des deux versions :  # Le module combine deux implémentations.
- génération : celle de collins (CSV en mémoire, pg_dump appelé sans shell) ;  # Génération des exports, reprise de la version de collins.
- historique : celui de tete-work (chaque export est écrit dans BACKUP_DIR et  # Historique, reprise de la version de tete-work.
  tracé dans la table `backups`, puis retéléchargeable).  # Chaque export est tracé en base et peut être retéléchargé.

Formats :  # Liste des formats d'export disponibles.
- CSV : une archive ZIP contenant un fichier CSV par table.  # Format CSV : archive ZIP avec un CSV par table.
- SQL : un dump complet produit par l'outil officiel pg_dump.  # Format SQL : dump complet généré par pg_dump.
"""  # Fin du docstring du module.
import csv  # Module standard pour écrire les fichiers CSV.
import os  # Accès aux variables d'environnement du processus.
import subprocess  # Lancement de la commande pg_dump.
import uuid  # Génération d'identifiants uniques pour les sauvegardes.
from datetime import datetime, timezone  # Date et heure, et fuseau UTC pour l'horodatage.
from io import StringIO  # Tampon texte en mémoire pour construire les CSV.
from pathlib import Path  # Manipulation des chemins de fichiers.
from uuid import UUID  # Type des identifiants de sauvegarde.
from zipfile import ZIP_DEFLATED, ZipFile  # Création d'archives ZIP compressées.

from sqlalchemy import select  # Construction de requêtes SELECT SQLAlchemy.
from sqlalchemy.engine import make_url  # Découpage d'une URL de base de données en ses composants.
from sqlalchemy.orm import Session  # Type de la session SQLAlchemy.

from app.core.config import settings  # Paramètres de l'application (URL de la base, dossier de sauvegarde).
from app.core.exceptions import AppError, NotFoundError, ServiceUnavailableError  # Erreurs métier utilisées dans ce module.
from app.db.base_class import Base  # Classe de base déclarative contenant la liste des tables.
from app.models import Backup, BackupFormat, User  # Modèle de sauvegarde, énumération des formats et modèle utilisateur.

def backup_dir() -> Path:  # Retourne le dossier de stockage des sauvegardes.
    path = Path(settings.BACKUP_DIR)  # Convertit le réglage de configuration en chemin.
    path.mkdir(parents=True, exist_ok=True)  # Crée le dossier et ses parents s'ils n'existent pas.
    return path  # Retourne le chemin du dossier.

def _write_csv_zip(db: Session, target: Path) -> None:  # Écrit l'archive ZIP contenant un CSV par table.
    with ZipFile(target, "w", ZIP_DEFLATED) as zip_file:  # Ouvre l'archive ZIP compressée en écriture.
        connection = db.connection()  # Connexion SQL de la session, pour exécuter les SELECT.
        for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):  # Parcourt les tables triées par nom.
            output = StringIO(newline="")  # Tampon texte en mémoire pour le CSV de cette table.
            writer = csv.writer(output)  # Écrivain CSV branché sur le tampon.
            writer.writerow(column.name for column in table.columns)  # en-têtes  # Écrit la ligne des noms de colonnes.
            writer.writerows(connection.execute(select(table)).fetchall())  # Écrit toutes les lignes de la table.
            zip_file.writestr(f"{table.name}.csv", output.getvalue())  # Ajoute le CSV à l'archive sous le nom de la table.

def _write_sql_dump(target: Path) -> None:  # Lance pg_dump et écrit le dump SQL dans le fichier cible.
    """  # Début du docstring de la fonction.
    Lance pg_dump vers `target`.  # Description : exécute pg_dump vers le fichier cible.

    Sécurité : la commande est passée sous forme de liste (pas de shell),  # Explication de la sécurité.
    ce qui empêche toute injection de commande ; le mot de passe passe par  # Pas de shell, donc pas d'injection de commande.
    la variable PGPASSWORD et n'apparaît pas dans la ligne de commande.  # Le mot de passe n'apparaît pas dans la ligne de commande.
    """  # Fin du docstring de la fonction.
    url = make_url(settings.DATABASE_URL)  # Découpe l'URL de connexion en ses composants.
    if url.get_backend_name() != "postgresql":  # Vérifie que la base est bien PostgreSQL.
        error = AppError("Les exports SQL nécessitent PostgreSQL.")  # Crée l'erreur pour une base non PostgreSQL.
        error.status_code = 501  # Code HTTP 501 : fonctionnalité non implémentée pour ce moteur.
        raise error  # Interrompt l'export.

    environment = os.environ.copy()  # Copie l'environnement du processus pour ne pas le modifier.
    if url.password is not None:  # Si l'URL contient un mot de passe.
        environment["PGPASSWORD"] = url.password  # Le transmet à pg_dump par variable d'environnement.

    command = ["pg_dump", "--no-owner", "--no-privileges", "--format=plain", "--file", str(target)]  # Commande pg_dump : sans propriétaires ni privilèges, au format texte, vers le fichier cible.
    if url.host:  # Si un hôte est indiqué dans l'URL.
        command += ["--host", url.host]  # Ajoute l'option d'hôte.
    if url.port:  # Si un port est indiqué dans l'URL.
        command += ["--port", str(url.port)]  # Ajoute l'option de port.
    if url.username:  # Si un nom d'utilisateur est indiqué dans l'URL.
        command += ["--username", url.username]  # Ajoute l'option d'utilisateur.
    command.append(url.database or "")  # Ajoute le nom de la base à sauvegarder (chaîne vide si absent).

    try:  # Tente d'exécuter pg_dump.
        subprocess.run(command, env=environment, check=True, capture_output=True, text=True, timeout=120)  # Lance la commande, avec erreur si elle échoue et délai maximal de 120 secondes.
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:  # Erreur système, échec de pg_dump ou délai dépassé.
        target.unlink(missing_ok=True)  # Supprime le fichier partiel éventuellement créé.
        raise ServiceUnavailableError("La création du backup SQL a échoué.") from exc  # Lève une erreur de service, en conservant la cause d'origine.

def create(db: Session, backup_format: BackupFormat, user: User) -> Backup:  # Génère le fichier puis enregistre l'export dans l'historique.
    """Génère le fichier, puis enregistre l'export dans l'historique."""  # Docstring : rôle de la fonction.
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # Horodatage UTC du nom de fichier, au format AAAAMMJJ_HHMMSS.
    backup_id = uuid.uuid4()  # Identifiant unique de la sauvegarde.
    extension = "sql" if backup_format == BackupFormat.SQL else "zip"  # Extension selon le format choisi.
    target = backup_dir() / f"camporga_{timestamp}_{backup_id.hex[:8]}.{extension}"  # Chemin final : préfixe, date, huit premiers caractères de l'identifiant, extension.

    if backup_format == BackupFormat.SQL:  # Format SQL demandé.
        _write_sql_dump(target)  # Génère le dump avec pg_dump.
    else:  # Sinon, format CSV.
        _write_csv_zip(db, target)  # Génère l'archive ZIP de CSV.

    backup = Backup(  # Crée l'enregistrement de l'export dans la base.
        id=backup_id,  # Identifiant de la sauvegarde.
        format=backup_format,  # Format de l'export.
        triggered_by=user.id,  # Utilisateur qui a lancé l'export.
        file_path=str(target),  # Chemin du fichier sur le disque.
        file_size_kb=max(1, target.stat().st_size // 1024),  # Taille en Ko, au minimum 1.
    )
    db.add(backup)  # Ajoute l'enregistrement à la session.
    db.commit()  # Enregistre en base.
    db.refresh(backup)  # Recharge l'enregistrement à jour.
    return backup  # Retourne la sauvegarde créée.

def list_backups(db: Session) -> list[Backup]:  # Liste l'historique des sauvegardes.
    return db.query(Backup).order_by(Backup.created_at.desc()).all()  # Toutes les sauvegardes, de la plus récente à la plus ancienne.

def get_file(db: Session, backup_id: UUID) -> Path:  # Retourne le chemin du fichier d'une sauvegarde.
    backup = db.get(Backup, backup_id)  # Recherche la sauvegarde par son identifiant.
    if backup is None:  # Sauvegarde absente de l'historique.
        raise NotFoundError("Sauvegarde introuvable.")  # Erreur 404.
    path = Path(backup.file_path).resolve()  # Chemin absolu du fichier, avec résolution des liens et des "..".
    # Défense en profondeur : on ne sert que des fichiers du dossier des sauvegardes.  # Protection supplémentaire contre les chemins hors du dossier.
    if backup_dir().resolve() not in path.parents or not path.exists():  # Fichier hors du dossier ou absent du disque.
        error = AppError("Le fichier de cette sauvegarde n'existe plus sur le serveur.")  # Crée l'erreur de fichier manquant.
        error.status_code = 410  # Code HTTP 410 : ressource disparue.
        raise error  # Interrompt la récupération.
    return path  # Retourne le chemin vérifié.