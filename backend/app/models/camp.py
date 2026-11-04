"""
Modèle Camp : la table centrale de CampOrga.

Un camp appartient à un organisateur (users) et regroupe ses modalités,
sa landing page, ses inscriptions et ses messages de contact.
cascade="all, delete-orphan" : supprimer un camp supprime aussi tout ce
qui en dépend, sans laisser de lignes orphelines.
"""  # Docstring du module : décrit le rôle du fichier et la notion de cascade de suppression.
import enum  # Module standard pour créer des énumérations (CampStatus).
import uuid  # Module standard pour générer des identifiants UUID.

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Text, func  # Types de colonnes SQLAlchemy, clé étrangère, Enum et fonction SQL func (ex. now()).
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre modèles.

from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class CampStatus(str, enum.Enum):  # Énumération des statuts d'un camp ; hériter de str facilite la sérialisation JSON.
    DRAFT = "draft"          # en préparation, invisible du public
    PUBLISHED = "published"  # visible, inscriptions ouvertes
    ARCHIVED = "archived"    # terminé, conservé pour l'historique

class Camp(Base):  # Modèle représentant un camp, hérite de Base.
    __tablename__ = "camps"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement à la création.
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Référence à l'organisateur (table users), obligatoire.
    name = Column(String, nullable=False)  # Nom du camp, obligatoire.
    # Le slug sert d'URL publique (ex. /camps/code-explorers-ete-2026) ;
    # l'index unique garantit qu'il n'y a pas deux camps à la même adresse.
    slug = Column(String, unique=True, index=True, nullable=False)  # Identifiant lisible pour l'URL, unique et indexé, obligatoire.
    description = Column(Text, nullable=True)  # Description libre du camp, facultative.
    start_date = Column(Date, nullable=False)  # Date de début du camp, obligatoire.
    end_date = Column(Date, nullable=False)  # Date de fin du camp, obligatoire.
    city = Column(String, nullable=False)  # Ville où se déroule le camp, obligatoire.
    # Âge minimum requis ("à partir de X ans") ; NULL = ouvert à tous les âges.
    # Les conditions plus fines (tranche d'âge, niveau) vont dans les modalités.
    age = Column(SmallInteger, nullable=True)  # Âge minimum, facultatif ; NULL signifie pas de restriction.
    capacity = Column(Integer, nullable=False)  # Nombre maximum de places, obligatoire.
    status = Column(Enum(CampStatus), default=CampStatus.DRAFT, nullable=False)  # Statut du camp, DRAFT par défaut, obligatoire.
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Date de création, remplie par la base, avec fuseau horaire.

    organizer = relationship("User", back_populates="camps")  # Accès à l'organisateur (objet User) ; back_populates relie à User.camps.
    registrations = relationship("Registration", back_populates="camp", cascade="all, delete-orphan")  # Liste des inscriptions ; supprimées avec le camp.
    modalities = relationship("CampModality", back_populates="camp", cascade="all, delete-orphan")  # Liste des modalités ; supprimées avec le camp.
    landing_page = relationship("LandingPage", back_populates="camp", uselist=False, cascade="all, delete-orphan")  # Une seule landing page (uselist=False) ; supprimée avec le camp.
    messages = relationship("ContactMessage", back_populates="camp", cascade="all, delete-orphan")  # Liste des messages de contact ; supprimés avec le camp.

    @property  # Permet d'accéder à la méthode comme à un attribut : camp.registrations_count.
    def registrations_count(self) -> int:  # Retourne un entier.
        """Nombre d'inscrits (calculé, non stocké : toujours à jour)."""  # Docstring : valeur calculée à la volée.
        return len(self.registrations)  # Compte les inscriptions chargées dans la relation.

    @property  # Propriété calculée, accessible comme un attribut.
    def remaining_places(self) -> int:  # Retourne le nombre de places restantes.
        """Places restantes affichées sur la landing page."""  # Docstring : usage prévu.
        return max(self.capacity - self.registrations_count, 0)  # Capacité moins inscrits, avec un minimum de 0 pour éviter les valeurs négatives.

    def __repr__(self):  # Représentation textuelle de l'objet, utile pour le débogage.
        return f"<Camp id={self.id!r} name={self.name!r}>"  # Affiche l'identifiant et le nom du camp.