import uuid  # Module standard pour générer des identifiants uniques (UUID).
import enum  # Module standard pour créer des énumérations (SeasonTheme).
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey  # Types de colonnes SQLAlchemy, dont Enum pour les valeurs fixes et ForeignKey pour les clés étrangères.
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre tables.
from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class SeasonTheme(str, enum.Enum):  # Énumération des thèmes saisonniers ; hériter de str permet la sérialisation JSON directe.
    SUMMER = "summer"  # Thème été.
    WINTER = "winter"  # Thème hiver.
    SPRING = "spring"  # Thème printemps.
    AUTUMN = "autumn"  # Thème automne.

class LandingPage(Base):  # Modèle représentant la page publique d'un camp, hérite de Base.
    __tablename__ = "landing_pages"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement à la création.
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False, unique=True)  # Référence au camp, clé étrangère unique : un camp n'a qu'une seule landing page (relation 1-1), obligatoire.
    season_theme = Column(Enum(SeasonTheme), nullable=False)  # Thème saisonnier de la page, valeur parmi SeasonTheme, obligatoire.
    hero_title = Column(String, nullable=False)  # Titre principal affiché en haut de la page, obligatoire.
    hero_description = Column(Text, nullable=True)  # Description affichée sous le titre, texte sans limite de longueur, facultatif.
    published_at = Column(DateTime(timezone=True), nullable=True)  # Date de publication ; vide tant que la page est en brouillon, avec fuseau horaire.

    camp = relationship("Camp", back_populates="landing_page")  # Accès à l'objet Camp associé ; back_populates relie cette relation à Camp.landing_page.