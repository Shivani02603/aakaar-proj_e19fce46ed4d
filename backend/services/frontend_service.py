from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Session, UploadedFile, Message
from sqlalchemy.orm import joinedload


class FrontendService:
    async def create_session(self, name: str, db: AsyncSession) -> Session:
        try:
            new_session = Session(name=name)
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")

    async def list_all_sessions(self, db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

    async def update_session(self, session_id: UUID, name: str, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            session.name = name
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

    async def get_session_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        try:
            result = await db.execute(
                select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
            )
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")

    async def create_message(self, session_id: UUID, role: str, content: str, citations: Optional[dict], db: AsyncSession) -> Message:
        try:
            new_message = Message(session_id=session_id, role=role, content=content, citations=citations)
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

    async def list_uploaded_files(self, session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list uploaded files: {str(e)}")

    async def upload_file(self, session_id: UUID, filename: str, file_path: str, file_size: int, db: AsyncSession) -> UploadedFile:
        try:
            new_file = UploadedFile(session_id=session_id, filename=filename, file_path=file_path, file_size=file_size)
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    async def delete_uploaded_file(self, file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete uploaded file: {str(e)}")