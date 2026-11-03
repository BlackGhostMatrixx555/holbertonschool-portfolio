"""
Modèle User : les comptes de la plateforme (super admin et organisateurs).

Fusion collins + tete-work : ajout du téléphone (vérification SMS) et des
champs de double authentification TOTP.
"""
import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SEM = "sem"
    SWE = "swe"
    SSM = "ssm"
    DC = "dc"   # directeur de campus
    DT = "dt"   # directeur technique (cahier des charges, section 2)
    ORGANIZER = "organizer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"   # ex. inscription en attente de validation
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.ORGANIZER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Double authentification (TOTP, compatible Google Authenticator, etc.).
    # Le secret n'est jamais renvoyé par l'API après l'activation.
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    camps = relationship("Camp", back_populates="organizer", cascade="all, delete-orphan")
    backups = relationship("Backup", back_populates="triggered_by_user")

    def __repr__(self):
        return f"<User {self.email}>"
