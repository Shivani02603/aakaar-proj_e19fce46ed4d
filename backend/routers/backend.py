from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/backend", tags=["Backend"])

# Pydantic Schemas
class UserBase(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID associated with the user")

class UserCreate(UserBase):
    password: str = Field(..., description="Password for the user")

class UserResponse(UserBase):
    id: UUID = Field(..., description="Unique identifier for the user")
    created_at: str = Field(..., description="Timestamp of user creation")

class SessionBase(BaseModel):
    name: str = Field(..., description="Name of the session")

class SessionCreate(SessionBase):
    user_id: UUID = Field(..., description="User ID associated with the session")

class SessionResponse(SessionBase):
    id: UUID = Field(..., description="Unique identifier for the session")
    created_at: str = Field(..., description="Timestamp of session creation")

class UploadedFileBase(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file")
    file_path: str = Field(..., description="Path to the uploaded file")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")

class UploadedFileCreate(UploadedFileBase):
    session_id: UUID = Field(..., description="Session ID associated with the uploaded file")

class UploadedFileResponse(UploadedFileBase):
    id: UUID = Field(..., description="Unique identifier for the uploaded file")
    uploaded_at: str = Field(..., description="Timestamp of file upload")

class DocumentChunkBase(BaseModel):
    content: str = Field(..., description="Content of the document chunk")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    start_row: int = Field(..., description="Start row of the chunk")
    end_row: int = Field(..., description="End row of the chunk")
    metadata: Optional[dict] = Field(None, description="Metadata associated with the chunk")

class DocumentChunkCreate(DocumentChunkBase):
    file_id: UUID = Field(..., description="File ID associated with the chunk")

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID = Field(..., description="Unique identifier for the document chunk")
    created_at: str = Field(..., description="Timestamp of chunk creation")

class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender (e.g., user, assistant)")
    content: str = Field(..., description="Content of the message")
    citations: Optional[dict] = Field(None, description="Citations associated with the message")

class MessageCreate(MessageBase):
    session_id: UUID = Field(..., description="Session ID associated with the message")

class MessageResponse(MessageBase):
    id: UUID = Field(..., description="Unique identifier for the message")
    created_at: str = Field(..., description="Timestamp of message creation")

# Endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    new_user = User(session_id=user.session_id, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse(id=new_user.id, session_id=new_user.session_id, created_at=new_user.created_at.isoformat())

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserResponse(id=user.id, session_id=user.session_id, created_at=user.created_at.isoformat()) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=user.id, session_id=user.session_id, created_at=user.created_at.isoformat())

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = Session(name=session.name, user_id=session.user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse(id=new_session.id, name=new_session.name, created_at=new_session.created_at.isoformat())

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(Session).all()
    return [SessionResponse(id=session.id, name=session.name, created_at=session.created_at.isoformat()) for session in sessions]

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionResponse(id=session.id, name=session.name, created_at=session.created_at.isoformat())

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()

@router.post("/uploaded-files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(file: UploadedFileCreate, db: Session = Depends(get_db)):
    new_file = UploadedFile(
        filename=file.filename,
        file_path=file.file_path,
        file_size=file.file_size,
        session_id=file.session_id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return UploadedFileResponse(
        id=new_file.id,
        filename=new_file.filename,
        file_path=new_file.file_path,
        file_size=new_file.file_size,
        uploaded_at=new_file.uploaded_at.isoformat(),
    )

@router.get("/uploaded-files", response_model=List[UploadedFileResponse])
def list_uploaded_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile).all()
    return [
        UploadedFileResponse(
            id=file.id,
            filename=file.filename,
            file_path=file.file_path,
            file_size=file.file_size,
            uploaded_at=file.uploaded_at.isoformat(),
        )
        for file in files
    ]

@router.get("/uploaded-files/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return UploadedFileResponse(
        id=file.id,
        filename=file.filename,
        file_path=file.file_path,
        file_size=file.file_size,
        uploaded_at=file.uploaded_at.isoformat(),
    )

@router.delete("/uploaded-files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()