from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from database.models import User, Session, UploadedFile, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/frontend", tags=["Frontend"])

# Pydantic Schemas
class FileUploadRequest(BaseModel):
    session_id: UUID
    filename: str
    file_path: str
    file_size: int

class FileUploadResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

class SessionCreateRequest(BaseModel):
    user_id: UUID
    name: str

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

class MessageCreateRequest(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict] = None

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict] = None
    created_at: datetime

# Endpoints

@router.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreateRequest, db: Session = Depends(get_db)):
    session = Session(
        id=UUID(),
        user_id=session_data.user_id,
        name=session_data.name,
        created_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(Session).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted successfully"}

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file_data: FileUploadRequest, db: Session = Depends(get_db)):
    uploaded_file = UploadedFile(
        id=UUID(),
        session_id=file_data.session_id,
        filename=file_data.filename,
        file_path=file_data.file_path,
        file_size=file_data.file_size,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    return uploaded_file

@router.get("/upload", response_model=List[FileUploadResponse])
async def list_uploaded_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return files

@router.get("/upload/{file_id}", response_model=FileUploadResponse)
async def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file)
    db.commit()
    return {"detail": "File deleted successfully"}

@router.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageCreateRequest, db: Session = Depends(get_db)):
    message = Message(
        id=UUID(),
        session_id=message_data.session_id,
        role=message_data.role,
        content=message_data.content,
        citations=message_data.citations,
        created_at=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/messages", response_model=List[MessageResponse])
async def list_messages(session_id: UUID = Query(...), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    return messages

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.delete("/messages/{message_id}")
async def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"detail": "Message deleted successfully"}