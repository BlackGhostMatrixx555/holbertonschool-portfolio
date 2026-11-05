"""
Modèle Backup : historique des exports de sauvegarde (apport de tete-work).

Chaque export est écrit dans un fichier sur le serveur et tracé ici :
format, taille, auteur et date. Le super admin peut ensuite le retélécharger.
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class BackupFormat(str, enum.Enum):
    SQL = "sql"
    CSV = "csv"


class Backup(Base):
    __tablename__ = "backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format = Column(Enum(BackupFormat), nullable=False)
    # RESTRICT : on ne peut pas supprimer un compte qui a déclenché des sauvegardes
    # (traçabilité : on doit toujours savoir qui a exporté les données).
    triggered_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    file_path = Column(String(500), nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    triggered_by_user = relationship("User", back_populates="backups")

    def __repr__(self):
        return f"<Backup {self.format.value} by {self.triggered_by}>"
