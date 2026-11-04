import uuid  # Module standard pour générer des identifiants UUID.
import enum  # Module standard pour créer des énumérations (ModalityType).
from sqlalchemy import Column, String, Enum, ForeignKey  # Colonne, type texte, type Enum SQLAlchemy et clé étrangère.
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre modèles.
from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class ModalityType(str, enum.Enum):  # Énumération des types de modalité ; hériter de str facilite la sérialisation JSON.
    AGE_RESTRICTION = "age_restriction"  # Restriction par tranche d'âge.
    EDUCATION_LEVEL = "education_level"  # Condition liée au niveau scolaire ou d'expérience.
    OTHER = "other"  # Autre type de modalité non catégorisé.
    INCLUDED = "included"  # Prestation incluse dans le prix du camp.
    OPTION = "option"  # Prestation proposée en option, à payer en plus.

class CampModality(Base):  # Modèle représentant une modalité rattachée à un camp, hérite de Base.
    __tablename__ = "camp_modalities"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement.
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)  # Référence au camp concerné (table camps), obligatoire.
    type = Column(Enum(ModalityType), nullable=False)  # Type de la modalité, selon l'énumération ModalityType, obligatoire.
    label = Column(String, nullable=False)  # Texte affiché décrivant la modalité, obligatoire.

    camp = relationship("Camp", back_populates="modalities")  # Accès au camp parent (objet Camp) ; back_populates relie à Camp.modalities.