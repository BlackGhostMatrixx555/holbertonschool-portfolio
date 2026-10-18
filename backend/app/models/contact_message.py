import uuid
import enum
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MessageStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class ContactChannel(str, enum.Enum):
    HOTLINE = "hotline"
    CHATBOT = "chatbot"

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(ContactChannel), default=ContactChannel.HOTLINE, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.UNREAD, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    camp = relationship("Camp", back_populates="messages")

    def __repr__(self):
        return f"<ContactMessage id={self.id!r} email={self.email!r}>"
