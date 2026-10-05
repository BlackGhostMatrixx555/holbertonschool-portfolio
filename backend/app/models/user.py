"""
Modèle User — les comptes de la plateforme (super admin + organisateurs).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, pg_enum
from app.models.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(pg_enum(UserRole, "user_role"), nullable=False)
    status = Column(
        pg_enum(UserStatus, "user_status"),
        nullable=False,
        default=UserStatus.INVITED,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Un utilisateur peut organiser plusieurs camps.
    # `back_populates` crée le lien dans les deux sens : user.camps et camp.organizer.
    camps = relationship("Camp", back_populates="organizer")
    backups = relationship("Backup", back_populates="triggered_by_user")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
