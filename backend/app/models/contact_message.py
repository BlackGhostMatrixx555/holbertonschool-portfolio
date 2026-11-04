import uuid  # Module standard pour générer des identifiants uniques (UUID).
import enum  # Module standard pour créer des énumérations (MessageStatus, ContactChannel).
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, func  # Types de colonnes SQLAlchemy, clé étrangère et fonction SQL func (ex. now()).
from sqlalchemy.dialects.postgresql import UUID  # Type UUID spécifique à PostgreSQL.
from sqlalchemy.orm import relationship  # Permet de déclarer les relations entre tables.
from app.db.base_class import Base  # Classe de base déclarative dont hérite le modèle.

class MessageStatus(str, enum.Enum):  # Énumération des statuts d'un message ; hériter de str permet la sérialisation JSON directe.
    UNREAD = "unread"  # Message non lu.
    READ = "read"  # Message lu.
    ARCHIVED = "archived"  # Message archivé.

class ContactChannel(str, enum.Enum):  # Énumération des canaux de contact.
    HOTLINE = "hotline"  # Contact par la ligne d'assistance téléphonique.
    CHATBOT = "chatbot"  # Contact par le chatbot.

class ContactMessage(Base):  # Modèle représentant un message envoyé à un camp, hérite de Base.
    __tablename__ = "contact_messages"  # Nom de la table dans la base de données.

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Clé primaire UUID, générée automatiquement à la création.
    camp_id = Column(UUID(as_uuid=True), ForeignKey("camps.id"), nullable=False)  # Référence au camp destinataire, clé étrangère vers la table camps, obligatoire.
    name = Column(String, nullable=False)  # Nom de l'expéditeur, obligatoire.
    email = Column(String, nullable=False)  # Adresse email de l'expéditeur, obligatoire.
    message = Column(Text, nullable=False)  # Contenu du message, texte sans limite de longueur, obligatoire.
    channel = Column(Enum(ContactChannel), default=ContactChannel.HOTLINE, nullable=False)  # Canal utilisé, HOTLINE par défaut, obligatoire.
    status = Column(Enum(MessageStatus), default=MessageStatus.UNREAD, nullable=False)  # Statut de traitement, UNREAD par défaut, obligatoire.
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Date d'envoi, remplie par la base avec l'heure courante, avec fuseau horaire.

    camp = relationship("Camp", back_populates="messages")  # Accès à l'objet Camp associé ; back_populates relie cette relation à Camp.messages.

    def __repr__(self):  # Représentation textuelle de l'objet, utile pour le débogage et les logs.
        return f"<ContactMessage id={self.id!r} email={self.email!r}>"  # Affiche l'identifiant et l'email de l'expéditeur.