"""
Énumérations utilisées par les modèles.

On les définit en Python avec `enum.Enum` : SQLAlchemy les traduira en types
ENUM PostgreSQL. L'avantage par rapport à de simples chaînes de caractères,
c'est que la base refuse toute valeur hors de cette liste — impossible
d'insérer un rôle "admiin" par faute de frappe.
"""
# enum : module standard Python pour créer des ensembles de valeurs fixes et nommées
import enum


# Rôles possibles d'un utilisateur sur la plateforme
# Hérite de str : les valeurs se comportent comme des chaînes, pratique pour le JSON et la base
class UserRole(str, enum.Enum):
    # Administrateur de la plateforme, accès total
    SUPER_ADMIN = "super_admin"
    # Rôle métier (sigle non explicité dans le code : à documenter)
    SEM = "sem"
    # Rôle métier (sigle non explicité dans le code : à documenter)
    SWE = "swe"
    # Rôle métier (sigle non explicité dans le code : à documenter)
    SSM = "ssm"
    # Directeur de campus, responsable d'un camp sur le terrain
    DIRECTEUR_CAMPUS = "directeur_campus"
    # Directeur technique, responsable du contenu pédagogique
    DIRECTEUR_TECHNIQUE = "directeur_technique"


# Cycle de vie d'un compte utilisateur
class UserStatus(str, enum.Enum):
    # Compte actif, peut se connecter
    ACTIVE = "active"
    # Compte créé mais pas encore activé par l'invité
    INVITED = "invited"
    # Compte désactivé, connexion refusée
    DISABLED = "disabled"


# Cycle de vie d'un camp
class CampStatus(str, enum.Enum):
    # Brouillon, non visible du public
    DRAFT = "draft"
    # Publié, visible et ouvert aux inscriptions
    PUBLISHED = "published"
    # Archivé, terminé ou retiré de la vitrine
    ARCHIVED = "archived"


# Types de modalités d'éligibilité d'un camp
class ModalityType(str, enum.Enum):
    # Restriction d'âge
    AGE_RESTRICTION = "age_restriction"
    # Niveau d'études requis
    EDUCATION_LEVEL = "education_level"
    # Autre condition libre
    OTHER = "other"


# Thèmes visuels saisonniers de la landing page
class SeasonTheme(str, enum.Enum):
    PRINTEMPS = "printemps"
    ETE = "ete"
    AUTOMNE = "automne"
    HIVER = "hiver"


# Canaux de contact proposés aux visiteurs
class ContactChannel(str, enum.Enum):
    # Formulaire de contact avec un humain
    HOTLINE = "hotline"
    # Assistant automatisé
    CHATBOT = "chatbot"


# Formats d'export de sauvegarde de la base
class BackupFormat(str, enum.Enum):
    # Dump SQL, restaurable directement dans PostgreSQL
    SQL = "sql"
    # Export tabulaire, lisible dans un tableur
    CSV = "csv"
