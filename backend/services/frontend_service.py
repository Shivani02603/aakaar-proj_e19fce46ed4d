from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Session, UploadedFile, Message, DocumentChunk


class FrontendService:
    async def create_session(self, session_data: dict, db: AsyncSession) -> Session:
        try:
            new_session = Session(**session_data)
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

    async def update_session(self, session_id: UUID, updated_data: dict, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            for key, value in updated_data.items():
                setattr(session, key, value)
            db.add(session)
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
            result = await db.execute(select(Message).where(Message.session_id == session_id))
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")

    async def get_uploaded_files(self, session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve uploaded files: {str(e)}")

    async def get_document_chunks(self, file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve document chunks: {str(e)}")