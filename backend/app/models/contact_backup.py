"""
Modèles ContactMessage et Backup — messages de contact et historique des
exports de sauvegarde.

⚠️ Fichier reconstitué d'après le schéma SQL et les relations déclarées
dans les autres modèles (`Backup.triggered_by_user`, `ContactMessage.camp`).
Si la version d'origine différait, adapte les noms de relations.
"""
import uuid

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, pg_enum
from app.models.enums import ContactChannel, BackupFormat


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("camps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(150))
    email = Column(String(255))
    message = Column(Text, nullable=False)
    channel = Column(pg_enum(ContactChannel, "contact_channel"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    camp = relationship("Camp", back_populates="contact_messages")

    def __repr__(self) -> str:
        return f"<ContactMessage {self.channel.value} from {self.email}>"


class Backup(Base):
    __tablename__ = "backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    format = Column(pg_enum(BackupFormat, "backup_format"), nullable=False)
    triggered_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    file_path = Column(String(500), nullable=False)
    file_size_kb = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Le nom de la relation doit correspondre à `back_populates="triggered_by_user"`
    # déclaré dans User.backups.
    triggered_by_user = relationship("User", back_populates="backups")

    def __repr__(self) -> str:
        return f"<Backup {self.format.value} by {self.triggered_by}>"
