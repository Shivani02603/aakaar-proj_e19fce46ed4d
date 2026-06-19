from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session, UploadedFile, Message
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.upload_service import upload_file
from backend.services.session_service import create_session, list_sessions, get_session_by_id, update_session, delete_session
from backend.services.frontend_service import get_session_messages, create_message

router = APIRouter(prefix="/api", tags=["Frontend"])

# Pydantic Schemas
class SessionCreateRequest(BaseModel):
    title: str = Field(..., example="New Session")

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: str

class MessageCreateRequest(BaseModel):
    sessionId: UUID
    role: str = Field(..., example="user")
    content: str = Field(..., example="What is the capital of France?")
    citations: Optional[dict] = Field(None, example={"source": "Wikipedia"})

class MessageResponse(BaseModel):
    id: UUID
    sessionId: UUID
    role: str
    content: str
    citations: Optional[dict]
    created_at: str

class UploadedFileResponse(BaseModel):
    id: UUID
    sessionId: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: str

# Endpoints
@router.post("/sessions", response_model=SessionResponse)
async def create_session_endpoint(
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await create_session(session_data, db)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = await list_sessions(db)
    return sessions

@router.get("/sessions/{sessionId}", response_model=SessionResponse)
async def get_session_endpoint(
    sessionId: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await get_session_by_id(sessionId, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/sessions/{sessionId}", response_model=SessionResponse)
async def update_session_endpoint(
    sessionId: UUID,
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await update_session(sessionId, session_data, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{sessionId}")
async def delete_session_endpoint(
    sessionId: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await delete_session(sessionId, db)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted successfully"}

@router.get("/sessions/{sessionId}/messages", response_model=List[MessageResponse])
async def get_session_messages_endpoint(
    sessionId: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = await get_session_messages(sessionId, db)
    return messages

@router.post("/sessions/{sessionId}/messages", response_model=MessageResponse)
async def create_message_endpoint(
    message_data: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = await create_message(message_data, db)
    return message

@router.post("/upload", response_model=UploadedFileResponse)
async def upload_file_endpoint(
    sessionId: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploaded_file = await upload_file(sessionId, file, db)
    return uploaded_file