"""
Modèle Registration — les inscriptions des visiteurs à un camp.
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid

# Column : déclare une colonne ; String, Text, Boolean, DateTime : types SQL ; ForeignKey : clé étrangère vers une autre table
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles
from sqlalchemy.orm import relationship
# func : accès aux fonctions SQL côté base (ex. func.now())
from sqlalchemy.sql import func

# Base : classe mère de tous les modèles
from app.database import Base


# Déclaration de la classe Registration, qui correspond à la table registrations
class Registration(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "registrations"

    # Identifiant unique de l'inscription, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Lien vers le camp concerné : clé étrangère vers camps.id
    camp_id = Column(
        UUID(as_uuid=True),
        # ondelete="CASCADE" : si le camp est supprimé, ses inscriptions le sont aussi automatiquement
        ForeignKey("camps.id", ondelete="CASCADE"),
        # Obligatoire : une inscription doit toujours être rattachée à un camp
        nullable=False,
        # Index pour accélérer la recherche des inscriptions d'un camp donné
        index=True,
    )
    # Prénom du participant, limité à 100 caractères, obligatoire
    first_name = Column(String(100), nullable=False)
    # Nom du participant, limité à 100 caractères, obligatoire
    last_name = Column(String(100), nullable=False)
    # Email du participant, indexé pour des recherches rapides (ex. vérifier un doublon)
    email = Column(String(255), nullable=False, index=True)
    # Commentaire libre du participant, texte sans limite de longueur, facultatif
    comment = Column(Text)
    # Indique si le participant a confirmé sa venue, faux par défaut
    confirmed = Column(Boolean, nullable=False, default=False)
    # Date d'inscription, remplie automatiquement par la base au moment de l'insertion
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relations
    # Camp auquel l'inscription est rattachée (lien inverse défini dans Camp)
    camp = relationship("Camp", back_populates="registrations")
    # Paiement associé à cette inscription : uselist=False indique une relation 1 à 1
    payment = relationship("Payment", back_populates="registration", uselist=False)

    # Représentation textuelle de l'objet, utile pour le débogage et les logs
    def __repr__(self) -> str:
        # Affiche l'email et l'identifiant du camp
        return f"<Registration {self.email} for camp {self.camp_id}>"
