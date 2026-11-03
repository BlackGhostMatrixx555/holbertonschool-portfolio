"""
Modèle LandingPage — la page publique associée à un camp (relation 1-1).
"""
# uuid : pour générer des identifiants uniques au format UUID
import uuid

# Column : déclare une colonne ; String, Text, DateTime, ForeignKey : types et contraintes SQL
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
# UUID : type UUID spécifique à PostgreSQL
from sqlalchemy.dialects.postgresql import UUID
# relationship : déclare un lien entre deux modèles
from sqlalchemy.orm import relationship

# Base : classe mère des modèles ; pg_enum : crée un type ENUM PostgreSQL à partir des valeurs Python
from app.database import Base, pg_enum
# Énumération des thèmes saisonniers (ex. été, hiver)
from app.models.enums import SeasonTheme


# Déclaration de la classe LandingPage, qui correspond à la table landing_pages
class LandingPage(Base):
    # Nom de la table dans PostgreSQL
    __tablename__ = "landing_pages"

    # Identifiant unique de la landing page, généré automatiquement au format UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # `unique=True` sur la clé étrangère : c'est ce qui garantit la relation
    # 1-1 (un camp ne peut avoir qu'une seule landing page).
    camp_id = Column(
        UUID(as_uuid=True),
        # ondelete="CASCADE" : si le camp est supprimé, sa landing page l'est aussi
        ForeignKey("camps.id", ondelete="CASCADE"),
        # Obligatoire : une landing page doit toujours appartenir à un camp
        nullable=False,
        # Unicité : un seul enregistrement par camp, c'est la contrainte qui fait la relation 1-1
        unique=True,
    )
    # Thème visuel saisonnier, stocké en ENUM PostgreSQL ; ETE par défaut
    season_theme = Column(
        pg_enum(SeasonTheme, "season_theme"),
        nullable=False,
        default=SeasonTheme.ETE,
    )
    # Titre principal affiché en haut de la page, limité à 200 caractères, facultatif
    hero_title = Column(String(200))
    # Texte de présentation affiché sous le titre, sans limite de longueur, facultatif
    hero_description = Column(Text)
    # Date de publication : vide tant que la page n'est pas publiée, ce qui permet un brouillon
    published_at = Column(DateTime(timezone=True))

    # Camp auquel appartient la landing page (lien inverse défini dans Camp)
    camp = relationship("Camp", back_populates="landing_page")

    # Représentation textuelle de l'objet pour le débogage et les logs
    def __repr__(self) -> str:
        # Affiche le camp concerné et la valeur du thème
        return f"<LandingPage camp={self.camp_id} theme={self.season_theme.value}>"
