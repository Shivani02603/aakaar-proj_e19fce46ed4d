import os
from datetime import datetime
import uuid
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    UniqueConstraint,
    Index,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pgvector.sqlalchemy import Vector

DATABASE_URL_ENV = "DATABASE_URL"
DATABASE_URL = os.environ.get(DATABASE_URL_ENV)

if not DATABASE_URL:
    raise ValueError(f"Environment variable {DATABASE_URL_ENV} is not set.")

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, session_id={self.session_id}, created_at={self.created_at})>"

    __table_args__ = (
        Index("ix_users_session_id", "session_id"),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")
    uploaded_files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, name={self.name}, created_at={self.created_at})>"

    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
    )


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="uploaded_files")
    document_chunks = relationship("DocumentChunk", back_populates="uploaded_file", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UploadedFile(id={self.id}, session_id={self.session_id}, filename={self.filename}, file_path={self.file_path}, file_size={self.file_size}, uploaded_at={self.uploaded_at})>"

    __table_args__ = (
        Index("ix_uploaded_files_session_id", "session_id"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    start_row = Column(Integer, nullable=False)
    end_row = Column(Integer, nullable=False)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    uploaded_file = relationship("UploadedFile", back_populates="document_chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, file_id={self.file_id}, chunk_index={self.chunk_index}, start_row={self.start_row}, end_row={self.end_row}, created_at={self.created_at})>"

    __table_args__ = (
        Index("ix_document_chunks_file_id", "file_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role}, created_at={self.created_at})>"

    __table_args__ = (
        Index("ix_messages_session_id", "session_id"),
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role_valid"),
    )