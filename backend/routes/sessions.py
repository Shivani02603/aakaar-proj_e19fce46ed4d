from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Session as DBSession, Message
from database.config import get_db

router = APIRouter()

# Pydantic Schemas
class SessionCreate(BaseModel):
    name: str = Field(..., example="New Session")

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: str

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: dict | None
    created_at: str

# Endpoints
@router.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    new_session = DBSession(name=session_data.name)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse(
        id=new_session.id,
        user_id=new_session.user_id,
        name=new_session.name,
        created_at=new_session.created_at.isoformat(),
    )

@router.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DBSession).all()
    return [
        SessionResponse(
            id=session.id,
            user_id=session.user_id,
            name=session.name,
            created_at=session.created_at.isoformat(),
        )
        for session in sessions
    ]

@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at.isoformat(),
    )

@router.get("/api/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    return [
        MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at.isoformat(),
        )
        for message in messages
    ]