from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/database", tags=["Database"])

# Pydantic Schemas
class UserBase(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID associated with the user")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: str

class SessionBase(BaseModel):
    name: str = Field(..., description="Name of the session")

class SessionCreate(SessionBase):
    user_id: UUID

class SessionResponse(SessionBase):
    id: UUID
    created_at: str

class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    file_path: str
    file_size: int

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    uploaded_at: str

class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    chunk_index: int
    start_row: int
    end_row: int
    metadata: Optional[dict] = Field(None, description="Additional metadata")

class DocumentChunkCreate(DocumentChunkBase):
    embedding: List[float]

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: str

class MessageBase(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict] = Field(None, description="Citations for the message")

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: UUID
    created_at: str

# CRUD Endpoints for User
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(db_user)
    db.commit()
    return None

# CRUD Endpoints for Session
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    db_session = Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(Session).all()

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session: SessionCreate, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    for key, value in session.dict().items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return None

# CRUD Endpoints for UploadedFile
@router.post("/uploaded_files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def create_uploaded_file(file: UploadedFileCreate, db: Session = Depends(get_db)):
    db_file = UploadedFile(**file.dict())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/uploaded_files", response_model=List[UploadedFileResponse])
def list_uploaded_files(db: Session = Depends(get_db)):
    return db.query(UploadedFile).all()

@router.get("/uploaded_files/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    return file

@router.put("/uploaded_files/{file_id}", response_model=UploadedFileResponse)
def update_uploaded_file(file_id: UUID, file: UploadedFileCreate, db: Session = Depends(get_db)):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    for key, value in file.dict().items():
        setattr(db_file, key, value)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.delete("/uploaded_files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db)):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    db.delete(db_file)
    db.commit()
    return None

# CRUD Endpoints for DocumentChunk
@router.post("/document_chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
def create_document_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    db_chunk = DocumentChunk(**chunk.dict())
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

@router.get("/document_chunks", response_model=List[DocumentChunkResponse])
def list_document_chunks(db: Session = Depends(get_db)):
    return db.query(DocumentChunk).all()

@router.get("/document_chunks/{chunk_id}", response_model=DocumentChunkResponse)
def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    return chunk

@router.put("/document_chunks/{chunk_id}", response_model=DocumentChunkResponse)
def update_document_chunk(chunk_id: UUID, chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    db_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    for key, value in chunk.dict().items():
        setattr(db_chunk, key, value)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

@router.delete("/document_chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    db_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    db.delete(db_chunk)
    db.commit()
    return None

# CRUD Endpoints for Message
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/messages", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db)):
    return db.query(Message).all()

@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(message_id: UUID, message: MessageCreate, db: Session = Depends(get_db)):
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    for key, value in message.dict().items():
        setattr(db_message, key, value)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID, db: Session = Depends(get_db)):
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(db_message)
    db.commit()
    return None