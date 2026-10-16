import uuid
import enum
from sqlalchemy import Column, String, Text, Date, SmallInteger, Integer, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class CampStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Camp(Base):
    __tablename__ = "camps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    city = Column(String, nullable=False)
    min_age = Column(SmallInteger, nullable=False)
    max_age = Column(SmallInteger, nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(CampStatus), default=CampStatus.DRAFT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organizer = relationship("User", back_populates="camps")
    registrations = relationship("Registration", back_populates="camp", cascade="all, delete-orphan")
    modalities = relationship("CampModality", back_populates="camp", cascade="all, delete-orphan")
    landing_page = relationship("LandingPage", back_populates="camp", uselist=False, cascade="all, delete-orphan")
    messages = relationship("ContactMessage", back_populates="camp", cascade="all, delete-orphan")
