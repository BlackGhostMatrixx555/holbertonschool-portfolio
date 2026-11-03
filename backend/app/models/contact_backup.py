"""
Modèles ContactMessage et Backup — messages de contact et historique des
exports de sauvegarde.

⚠️ Fichier reconstitué d'après le schéma SQL et les relations déclarées
dans les autres modèles (`Backup.triggered_by_user`, `ContactMessage.camp`).
Si la version d'origine différait, adapte les noms de relations.
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid

# Column : déclare une colonne ; types et contraintes SQL utilisés ici
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles
from sqlalchemy.orm import relationship
# func : fonctions SQL exécutées côté base (ici now() pour l'horodatage)
from sqlalchemy.sql import func

# Base : classe mère des modèles ; pg_enum : crée un type ENUM PostgreSQL à partir des valeurs Python
from app.database import Base, pg_enum
# Énumérations des canaux de contact et des formats de sauvegarde
from app.models.enums import ContactChannel, BackupFormat


# Déclaration de la classe ContactMessage, qui correspond à la table contact_messages
class ContactMessage(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "contact_messages"

    # Identifiant unique du message, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Camp concerné par le message : facultatif, car la hotline peut être générale
    camp_id = Column(
        UUID(as_uuid=True),
        # ondelete="SET NULL" : si le camp est supprimé, le message est conservé mais détaché
        ForeignKey("camps.id", ondelete="SET NULL"),
        # Peut être vide : un message général n'est lié à aucun camp
        nullable=True,
        # Index pour retrouver rapidement les messages d'un camp
        index=True,
    )
    # Nom de l'expéditeur, limité à 150 caractères
    name = Column(String(150))
    # Adresse email de l'expéditeur pour la réponse
    email = Column(String(255))
    # Contenu du message, sans limite de longueur, obligatoire
    message = Column(Text, nullable=False)
    # Canal d'origine du message (hotline ou chatbot), stocké en ENUM PostgreSQL
    channel = Column(pg_enum(ContactChannel, "contact_channel"), nullable=False)
    # Date de réception, renseignée automatiquement par la base au moment de l'insertion
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Camp concerné par le message (lien inverse défini dans Camp)
    camp = relationship("Camp", back_populates="contact_messages")

    # Représentation textuelle pour le débogage et les logs
    def __repr__(self) -> str:
        return f"<ContactMessage {self.channel.value} from {self.email}>"


# Déclaration de la classe Backup, qui correspond à la table backups
class Backup(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "backups"

    # Identifiant unique de la sauvegarde, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Format de l'export : SQL ou CSV, stocké en ENUM PostgreSQL
    format = Column(pg_enum(BackupFormat, "backup_format"), nullable=False)
    # Utilisateur ayant déclenché la sauvegarde : clé étrangère vers users.id
    triggered_by = Column(
        UUID(as_uuid=True),
        # ondelete="RESTRICT" : impossible de supprimer un utilisateur ayant déclenché une sauvegarde, pour préserver la traçabilité
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        # Index pour retrouver rapidement les sauvegardes d'un utilisateur
        index=True,
    )
    # Chemin du fichier généré sur le serveur, limité à 500 caractères
    file_path = Column(String(500), nullable=False)
    # Taille du fichier en kilo-octets, facultative (non renseignée si la génération échoue)
    file_size_kb = Column(Integer)
    # Date de création, renseignée automatiquement par la base
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Utilisateur qui a déclenché la sauvegarde
    # Le nom de la relation doit correspondre à `back_populates="triggered_by_user"`
    # déclaré dans User.backups.
    triggered_by_user = relationship("User", back_populates="backups")

    # Représentation textuelle pour le débogage et les logs
    def __repr__(self) -> str:
        # Affiche le format et l'identifiant de l'auteur de la sauvegarde
        return f"<Backup {self.format.value} by {self.triggered_by}>"
