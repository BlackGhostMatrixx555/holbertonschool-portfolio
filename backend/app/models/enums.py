"""
Énumérations utilisées par les modèles.

On les définit en Python avec `enum.Enum` : SQLAlchemy les traduira en types
ENUM PostgreSQL. L'avantage par rapport à de simples chaînes de caractères,
c'est que la base refuse toute valeur hors de cette liste — impossible
d'insérer un rôle "admiin" par faute de frappe.
"""
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    SEM = "sem"
    SWE = "swe"
    SSM = "ssm"
    DIRECTEUR_CAMPUS = "directeur_campus"
    DIRECTEUR_TECHNIQUE = "directeur_technique"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"


class CampStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ModalityType(str, enum.Enum):
    AGE_RESTRICTION = "age_restriction"
    EDUCATION_LEVEL = "education_level"
    OTHER = "other"


class SeasonTheme(str, enum.Enum):
    PRINTEMPS = "printemps"
    ETE = "ete"
    AUTOMNE = "automne"
    HIVER = "hiver"


class ContactChannel(str, enum.Enum):
    HOTLINE = "hotline"
    CHATBOT = "chatbot"


class BackupFormat(str, enum.Enum):
    SQL = "sql"
    CSV = "csv"
