from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from database.models import User, Session as DBSession, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/database", tags=["Database"])

# Pydantic schemas
class UserSchema(BaseModel):
    id: UUID
    session_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    session_id: str

class UserUpdate(BaseModel):
    session_id: Optional[str]

class SessionSchema(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    user_id: UUID
    name: str

class SessionUpdate(BaseModel):
    name: Optional[str]

class UploadedFileSchema(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

    class Config:
        orm_mode = True

class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    file_path: str
    file_size: int

class UploadedFileUpdate(BaseModel):
    filename: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]

class DocumentChunkSchema(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict
    created_at: datetime

    class Config:
        orm_mode = True

class DocumentChunkCreate(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict

class DocumentChunkUpdate(BaseModel):
    content: Optional[str]
    embedding: Optional[List[float]]
    chunk_index: Optional[int]
    start_row: Optional[int]
    end_row: Optional[int]
    metadata: Optional[dict]

class MessageSchema(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: dict
    created_at: datetime

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: dict

class MessageUpdate(BaseModel):
    role: Optional[str]
    content: Optional[str]
    citations: Optional[dict]

# CRUD endpoints for User
@router.get("/users", response_model=List[UserSchema])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user: UserUpdate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict(exclude_unset=True).items():
        setattr(existing_user, key, value)
    db.commit()
    db.refresh(existing_user)
    return existing_user

@router.delete("/users/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}

# CRUD endpoints for Session
@router.get("/sessions", response_model=List[SessionSchema])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DBSession).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionSchema)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/sessions", response_model=SessionSchema)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = DBSession(**session.dict())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.put("/sessions/{session_id}", response_model=SessionSchema)
def update_session(session_id: UUID, session: SessionUpdate, db: Session = Depends(get_db)):
    existing_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not existing_session:
        raise HTTPException(status_code=404, detail="Session not found")
    for key, value in session.dict(exclude_unset=True).items():
        setattr(existing_session, key, value)
    db.commit()
    db.refresh(existing_session)
    return existing_session

@router.delete("/sessions/{session_id}")
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted successfully"}

# CRUD endpoints for UploadedFile
@router.get("/uploaded_files", response_model=List[UploadedFileSchema])
def list_uploaded_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files

@router.get("/uploaded_files/{file_id}", response_model=UploadedFileSchema)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    return file

@router.post("/uploaded_files", response_model=UploadedFileSchema)
def create_uploaded_file(file: UploadedFileCreate, db: Session = Depends(get_db)):
    new_file = UploadedFile(**file.dict())
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file

@router.put("/uploaded_files/{file_id}", response_model=UploadedFileSchema)
def update_uploaded_file(file_id: UUID, file: UploadedFileUpdate, db: Session = Depends(get_db)):
    existing_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not existing_file:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    for key, value in file.dict(exclude_unset=True).items():
        setattr(existing_file, key, value)
    db.commit()
    db.refresh(existing_file)
    return existing_file

@router.delete("/uploaded_files/{file_id}")
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    db.delete(file)
    db.commit()
    return {"detail": "Uploaded file deleted successfully"}

# CRUD endpoints for DocumentChunk
@router.get("/document_chunks", response_model=List[DocumentChunkSchema])
def list_document_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return chunks

@router.get("/document_chunks/{chunk_id}", response_model=DocumentChunkSchema)
def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    return chunk

@router.post("/document_chunks", response_model=DocumentChunkSchema)
def create_document_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    new_chunk = DocumentChunk(**chunk.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return new_chunk

@router.put("/document_chunks/{chunk_id}", response_model=DocumentChunkSchema)
def update_document_chunk(chunk_id: UUID, chunk: DocumentChunkUpdate, db: Session = Depends(get_db)):
    existing_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not existing_chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    for key, value in chunk.dict(exclude_unset=True).items():
        setattr(existing_chunk, key, value)
    db.commit()
    db.refresh(existing_chunk)
    return existing_chunk

@router.delete("/document_chunks/{chunk_id}")
def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found")
    db.delete(chunk)
    db.commit()
    return {"detail": "Document chunk deleted successfully"}

# CRUD endpoints for Message
@router.get("/messages", response_model=List[MessageSchema])
def list_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).all()
    return messages

@router.get("/messages/{message_id}", response_model=MessageSchema)
def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.post("/messages", response_model=MessageSchema)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(**message.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.put("/messages/{message_id}", response_model=MessageSchema)
def update_message(message_id: UUID, message: MessageUpdate, db: Session = Depends(get_db)):
    existing_message = db.query(Message).filter(Message.id == message_id).first()
    if not existing_message:
        raise HTTPException(status_code=404, detail="Message not found")
    for key, value in message.dict(exclude_unset=True).items():
        setattr(existing_message, key, value)
    db.commit()
    db.refresh(existing_message)
    return existing_message

@router.delete("/messages/{message_id}")
def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"detail": "Message deleted successfully"}