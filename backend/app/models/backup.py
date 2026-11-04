"""
Modèle Backup : historique des exports de sauvegarde (apport de tete-work).

Chaque export est écrit dans un fichier sur le serveur et tracé ici :
format, taille, auteur et date. Le super admin peut ensuite le retélécharger.
"""  # Docstring du module : rôle du fichier et traçabilité des exports.
import enum  # Module standard pour créer des énumérations (BackupFormat).
import uuid  # Module standard pour générer des identifiants UUID.

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func  # Types de colonnes, clé étrangère, Enum et fonction SQL func (ex. now()).
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre modèles.

from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class BackupFormat(str, enum.Enum):  # Énumération des formats d'export ; hériter de str facilite la sérialisation JSON.
    SQL = "sql"  # Export sous forme de script SQL.
    CSV = "csv"  # Export sous forme de fichiers CSV.

class Backup(Base):  # Modèle représentant une sauvegarde exportée, hérite de Base.
    __tablename__ = "backups"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement.
    format = Column(Enum(BackupFormat), nullable=False)  # Format de l'export (SQL ou CSV), obligatoire.
    # RESTRICT : on ne peut pas supprimer un compte qui a déclenché des sauvegardes
    # (traçabilité : on doit toujours savoir qui a exporté les données).
    triggered_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )  # Identifiant de l'utilisateur ayant déclenché l'export ; RESTRICT empêche la suppression de ce compte, index pour accélérer les recherches.
    file_path = Column(String(500), nullable=False)  # Chemin du fichier exporté sur le serveur, 500 caractères max, obligatoire.
    file_size_kb = Column(Integer, nullable=True)  # Taille du fichier en kilo-octets, facultative.
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Date de création de l'export, remplie par la base, avec fuseau horaire.

    triggered_by_user = relationship("User", back_populates="backups")  # Accès à l'utilisateur ayant déclenché l'export ; back_populates relie à User.backups.

    def __repr__(self):  # Représentation textuelle de l'objet, utile pour le débogage.
        return f"<Backup {self.format.value} by {self.triggered_by}>"  # Affiche le format de l'export et l'identifiant de son auteur.