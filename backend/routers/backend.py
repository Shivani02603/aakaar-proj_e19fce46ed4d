from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from database.models import User, Session, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/backend", tags=["Backend"])

# Pydantic schemas
class UserCreate(BaseModel):
    session_id: str

class UserResponse(BaseModel):
    id: UUID
    session_id: str
    created_at: datetime

class SessionCreate(BaseModel):
    user_id: UUID
    name: str

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    file_path: str
    file_size: int

class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

class DocumentChunkCreate(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict

class DocumentChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict
    created_at: datetime

class MessageCreate(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: dict

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: dict
    created_at: datetime

# CRUD endpoints for User
@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(session_id=user.session_id, created_at=datetime.utcnow())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/users/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}

# CRUD endpoints for Session
@router.post("/sessions", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = Session(user_id=session.user_id, name=session.name, created_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(Session).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted successfully"}

# CRUD endpoints for UploadedFile
@router.post("/uploaded_files", response_model=UploadedFileResponse)
def create_uploaded_file(file: UploadedFileCreate, db: Session = Depends(get_db)):
    new_file = UploadedFile(
        session_id=file.session_id,
        filename=file.filename,
        file_path=file.file_path,
        file_size=file.file_size,
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file

@router.get("/uploaded_files", response_model=List[UploadedFileResponse])
def list_uploaded_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files

@router.get("/uploaded_files/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    return file

@router.delete("/uploaded_files/{file_id}")
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    db.delete(file)
    db.commit()
    return {"detail": "Uploaded file deleted successfully"}

# CRUD endpoints for DocumentChunk
@router.post("/document_chunks", response_model=DocumentChunkResponse)
def create_document_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    new_chunk = DocumentChunk(
        file_id=chunk.file_id,
        content=chunk.content,
        embedding=chunk.embedding,
        chunk_index=chunk.chunk_index,
        start_row=chunk.start_row,
        end_row=chunk.end_row,
        metadata=chunk.metadata,
        created_at=datetime.utcnow(),
    )
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

@router.get("/document_chunks", response_model=List[DocumentChunkResponse])
def list_document_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return chunks

@router.get("/document_chunks/{chunk_id}", response_model=DocumentChunkResponse)
def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    return chunk

@router.delete("/document_chunks/{chunk_id}")
def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    db.delete(chunk)
    db.commit()
    return {"detail": "Document chunk deleted successfully"}

# CRUD endpoints for Message
@router.post("/messages", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        created_at=datetime.utcnow(),
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.get("/messages", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).all()
    return messages

@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.delete("/messages/{message_id}")
def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"detail": "Message deleted successfully"}