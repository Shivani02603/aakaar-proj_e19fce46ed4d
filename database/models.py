from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    created_at = Column(DateTime)

    session = relationship("Session", back_populates="users")

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, index=True)
    created_at = Column(DateTime)

    users = relationship("User", back_populates="session")
    messages = relationship("Message", back_populates="session")
    uploaded_files = relationship("UploadedFile", back_populates="session")

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Float)
    uploaded_at = Column(DateTime)

    session = relationship("Session", back_populates="uploaded_files")

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'))
    content = Column(Text)
    embedding = Column(Text)
    chunk_index = Column(Integer)
    start_row = Column(Integer)
    end_row = Column(Integer)
    metadata = Column(Text)
    created_at = Column(DateTime)

    uploaded_file = relationship("UploadedFile")

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    role = Column(String)
    content = Column(Text)
    citations = Column(Text)
    created_at = Column(DateTime)

    session = relationship("Session", back_populates="messages")

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)