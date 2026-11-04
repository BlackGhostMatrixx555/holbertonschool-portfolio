import uuid  # Module standard pour générer des identifiants uniques (UUID).
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func  # Types de colonnes SQLAlchemy, clé étrangère et fonction SQL func (ex. now()).
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre tables.
from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class Registration(Base):  # Modèle représentant l'inscription d'un visiteur à un camp, hérite de Base.
    __tablename__ = "registrations"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement à la création.
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)  # Référence au camp concerné, clé étrangère vers la table camps, obligatoire.
    first_name = Column(String, nullable=False)  # Prénom du visiteur, obligatoire.
    last_name = Column(String, nullable=False)  # Nom de famille du visiteur, obligatoire.
    email = Column(String, nullable=False)  # Adresse email du visiteur, obligatoire. Non unique : une même personne peut s'inscrire à plusieurs camps.
    comment = Column(Text, nullable=True)  # Commentaire libre, texte sans limite de longueur, facultatif.
    confirmed = Column(Boolean, default=False, nullable=False)  # Indique si la présence est confirmée, faux par défaut, obligatoire.
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Date d'inscription, remplie par la base avec l'heure courante, avec fuseau horaire.

    camp = relationship("Camp", back_populates="registrations")  # Accès à l'objet Camp associé ; back_populates relie cette relation à Camp.registrations.