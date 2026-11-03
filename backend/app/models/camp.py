"""
Modèles Camp et CampModality — la table centrale du schéma et ses critères
d'éligibilité.
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid

# Types et contraintes SQL utilisés pour déclarer les colonnes
from sqlalchemy import (
    Column, String, Text, Date, Integer, SmallInteger, DateTime,
    ForeignKey, CheckConstraint,
)
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles
from sqlalchemy.orm import relationship
# func : fonctions SQL exécutées côté base (ici now())
from sqlalchemy.sql import func

# Base : classe mère des modèles ; pg_enum : crée un type ENUM PostgreSQL à partir des valeurs Python
from app.database import Base, pg_enum
# Énumérations du statut d'un camp et des types de modalités
from app.models.enums import CampStatus, ModalityType


# Déclaration de la classe Camp, qui correspond à la table camps
class Camp(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "camps"

    # Identifiant unique du camp, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Organisateur responsable du camp : clé étrangère vers users.id
    organizer_id = Column(
        UUID(as_uuid=True),
        # ondelete="RESTRICT" : impossible de supprimer un organisateur qui possède encore des camps
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        # Index pour retrouver rapidement les camps d'un organisateur
        index=True,
    )
    # Nom du camp, limité à 150 caractères, obligatoire
    name = Column(String(150), nullable=False)
    # Version lisible du nom, utilisée dans l'URL publique (ex. /camps/ete-2026)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    # Description libre, facultative
    description = Column(Text)
    # Date de début du camp, obligatoire
    start_date = Column(Date, nullable=False)
    # Date de fin du camp, obligatoire
    end_date = Column(Date, nullable=False)
    # Ville où se déroule le camp, facultative
    city = Column(String(100))
    # Âge minimum (ou cible) des participants, petit entier suffisant pour une tranche d'âge
    age = Column(SmallInteger)
    # Nombre maximum de places ; 0 par défaut
    capacity = Column(Integer, nullable=False, default=0)
    # Prix en centimes pour éviter les erreurs d'arrondi des nombres à virgule
    price = Column(Integer, nullable=False, default=0)  # <-- Ajouté : prix en centimes
    # Statut de publication, brouillon par défaut, indexé pour filtrer rapidement
    status = Column(
        pg_enum(CampStatus, "camp_status"),
        nullable=False,
        default=CampStatus.DRAFT,
        index=True,
    )
    # Date de création, renseignée automatiquement par la base
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Contraintes au niveau table (et non colonne)
    __table_args__ = (
        # Vérifie en base que la date de fin n'est pas antérieure à la date de début
        CheckConstraint("end_date >= start_date", name="ck_camps_dates"),
    )

    # Organisateur du camp (lien inverse défini dans User)
    organizer = relationship("User", back_populates="camps")
    # Critères d'éligibilité du camp ; supprimés avec le camp (cascade)
    modalities = relationship(
        "CampModality", back_populates="camp", cascade="all, delete-orphan"
    )
    # Landing page publique, relation 1-1 ; supprimée avec le camp
    landing_page = relationship(
        "LandingPage", back_populates="camp", uselist=False, cascade="all, delete-orphan"
    )
    # Inscriptions reçues ; supprimées avec le camp
    registrations = relationship(
        "Registration", back_populates="camp", cascade="all, delete-orphan"
    )
    # Messages de contact liés au camp ; conservés si le camp est supprimé (voir ContactMessage)
    contact_messages = relationship("ContactMessage", back_populates="camp")

    # Représentation textuelle pour le débogage et les logs
    def __repr__(self) -> str:
        return f"<Camp {self.slug}>"


# Déclaration de la classe CampModality, qui correspond à la table camp_modalities
class CampModality(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "camp_modalities"

    # Identifiant unique de la modalité, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Camp auquel s'applique la modalité : clé étrangère vers camps.id
    camp_id = Column(
        UUID(as_uuid=True),
        # ondelete="CASCADE" : si le camp disparaît, ses modalités disparaissent aussi
        ForeignKey("camps.id", ondelete="CASCADE"),
        nullable=False,
        # Index pour charger rapidement les modalités d'un camp
        index=True,
    )
    # Type de la modalité (âge, niveau d'études, autre), stocké en ENUM PostgreSQL
    type = Column(pg_enum(ModalityType, "modality_type"), nullable=False)
    # Libellé lisible affiché au visiteur, limité à 255 caractères
    label = Column(String(255), nullable=False)

    # Camp auquel appartient la modalité (lien inverse défini dans Camp)
    camp = relationship("Camp", back_populates="modalities")

    # Représentation textuelle pour le débogage et les logs
    def __repr__(self) -> str:
        return f"<CampModality {self.type.value}: {self.label}>"
