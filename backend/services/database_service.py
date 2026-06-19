from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.models import User, Session, UploadedFile, DocumentChunk, Message

class DatabaseService:
    async def create_user(self, user: User, db: AsyncSession) -> User:
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

    async def list_all_users(self, db: AsyncSession) -> List[User]:
        try:
            result = await db.execute(select(User))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

    async def update_user(self, user_id: UUID, user_update: User, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            for key, value in user_update.dict(exclude_unset=True).items():
                setattr(user, key, value)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

    async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            await db.delete(user)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

    async def create_session(self, session: Session, db: AsyncSession) -> Session:
        try:
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

    async def list_all_sessions(self, db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

    async def update_session(self, session_id: UUID, session_update: Session, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            for key, value in session_update.dict(exclude_unset=True).items():
                setattr(session, key, value)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")

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
            raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

    async def create_uploaded_file(self, file: UploadedFile, db: AsyncSession) -> UploadedFile:
        try:
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating uploaded file: {str(e)}")

    async def get_uploaded_file_by_id(self, file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            return file
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving uploaded file: {str(e)}")

    async def list_uploaded_files(self, db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing uploaded files: {str(e)}")

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
            raise HTTPException(status_code=500, detail=f"Error deleting uploaded file: {str(e)}")

    async def create_document_chunk(self, chunk: DocumentChunk, db: AsyncSession) -> DocumentChunk:
        try:
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating document chunk: {str(e)}")

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving document chunk: {str(e)}")

    async def list_document_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing document chunks: {str(e)}")

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting document chunk: {str(e)}")

    async def create_message(self, message: Message, db: AsyncSession) -> Message:
        try:
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving message: {str(e)}")

    async def list_messages(self, db: AsyncSession) -> List[Message]:
        try:
            result = await db.execute(select(Message))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing messages: {str(e)}")

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            await db.delete(message)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")