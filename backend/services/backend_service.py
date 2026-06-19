from typing import List
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import User, Session
from sqlalchemy.orm import joinedload


class BackendService:
    async def create_user(self, user_data: dict, db: AsyncSession) -> User:
        try:
            new_user = User(**user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
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
            users = result.scalars().all()
            return users
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

    async def update_user(self, user_id: UUID, user_data: dict, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            for key, value in user_data.items():
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

    async def create_session(self, session_data: dict, db: AsyncSession) -> Session:
        try:
            new_session = Session(**session_data)
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id).options(joinedload(Session.user)))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

    async def list_all_sessions(self, db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session).options(joinedload(Session.user)))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

    async def update_session(self, session_id: UUID, session_data: dict, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            for key, value in session_data.items():
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