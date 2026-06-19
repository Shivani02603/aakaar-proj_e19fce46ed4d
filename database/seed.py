import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Session, UploadedFile, DocumentChunk, Message, SessionLocal


async def seed_database():
    async with SessionLocal() as session:
        try:
            # Insert Users
            user1 = User(id=uuid.uuid4(), session_id="session_001", created_at=datetime.utcnow())
            user2 = User(id=uuid.uuid4(), session_id="session_002", created_at=datetime.utcnow())
            user3 = User(id=uuid.uuid4(), session_id="session_003", created_at=datetime.utcnow())
            session.add_all([user1, user2, user3])
            await session.flush()

            # Insert Sessions
            session1 = Session(id=uuid.uuid4(), user_id=user1.id, name="Session A", created_at=datetime.utcnow())
            session2 = Session(id=uuid.uuid4(), user_id=user2.id, name="Session B", created_at=datetime.utcnow())
            session3 = Session(id=uuid.uuid4(), user_id=user3.id, name="Session C", created_at=datetime.utcnow())
            session.add_all([session1, session2, session3])
            await session.flush()

            # Insert UploadedFiles
            file1 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session1.id,
                filename="file1.txt",
                file_path="/uploads/file1.txt",
                file_size=1024,
                uploaded_at=datetime.utcnow()
            )
            file2 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session2.id,
                filename="file2.txt",
                file_path="/uploads/file2.txt",
                file_size=2048,
                uploaded_at=datetime.utcnow()
            )
            file3 = UploadedFile(
                id=uuid.uuid4(),
                session_id=session3.id,
                filename="file3.txt",
                file_path="/uploads/file3.txt",
                file_size=4096,
                uploaded_at=datetime.utcnow()
            )
            session.add_all([file1, file2, file3])
            await session.flush()

            # Insert DocumentChunks
            chunk1 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file1.id,
                content="This is the content of chunk 1.",
                embedding=None,
                chunk_index=0,
                start_row=1,
                end_row=10,
                metadata={"type": "text"},
                created_at=datetime.utcnow()
            )
            chunk2 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file2.id,
                content="This is the content of chunk 2.",
                embedding=None,
                chunk_index=1,
                start_row=11,
                end_row=20,
                metadata={"type": "text"},
                created_at=datetime.utcnow()
            )
            chunk3 = DocumentChunk(
                id=uuid.uuid4(),
                file_id=file3.id,
                content="This is the content of chunk 3.",
                embedding=None,
                chunk_index=2,
                start_row=21,
                end_row=30,
                metadata={"type": "text"},
                created_at=datetime.utcnow()
            )
            session.add_all([chunk1, chunk2, chunk3])
            await session.flush()

            # Insert Messages
            message1 = Message(
                id=uuid.uuid4(),
                session_id=session1.id,
                role="user",
                content="Hello, how can I help you?",
                citations=None,
                created_at=datetime.utcnow()
            )
            message2 = Message(
                id=uuid.uuid4(),
                session_id=session2.id,
                role="assistant",
                content="I need assistance with my account.",
                citations=None,
                created_at=datetime.utcnow()
            )
            message3 = Message(
                id=uuid.uuid4(),
                session_id=session3.id,
                role="system",
                content="System message: Your session has expired.",
                citations=None,
                created_at=datetime.utcnow()
            )
            session.add_all([message1, message2, message3])
            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")


if __name__ == "__main__":
    asyncio.run(seed_database())