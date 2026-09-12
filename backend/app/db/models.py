import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, default="New Growth Conversation")
    model_used = Column(String(100), nullable=False, default="ollama:mistral")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    meta_info = Column(JSON, nullable=True, default=dict)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan", order_by="ArtifactModel.created_at")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True, default=list)  # list of source objects
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("SessionModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False, default="Untitled Artifact")
    artifact_type = Column(String(50), nullable=False, default="markdown")  # html, markdown, code
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("SessionModel", back_populates="artifacts")
    message = relationship("MessageModel", back_populates="artifacts")
