from typing import List, Dict, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, Message, UploadedFile
from ai.embeddings import get_embedding
from ai.vector_store import VectorStore
from ai.rag import retrieve_context, answer_question
from env import GEMINI_API_KEY
import os

class QueryPipelineService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def embed_query(self, query: str) -> List[float]:
        try:
            embedding = get_embedding([query])
            return embedding[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

    async def retrieve_top_chunks(self, query_embedding: List[float], top_k: int, session_id: UUID, db: AsyncSession) -> List[Dict]:
        try:
            chunks = await self.vector_store.search(query_embedding, top_k)
            if not chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found.")
            
            # Fetch metadata for chunks
            chunk_ids = [chunk['id'] for chunk in chunks]
            stmt = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
            result = await db.execute(stmt)
            document_chunks = result.scalars().all()

            return [
                {
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "file_id": chunk.file_id,
                    "start_row": chunk.start_row,
                    "end_row": chunk.end_row
                }
                for chunk in document_chunks
            ]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve top chunks: {str(e)}")

    async def generate_answer(self, query: str, context: List[Dict], session_id: UUID, user_id: UUID) -> Dict:
        try:
            if not GEMINI_API_KEY:
                raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured.")

            # Prepare context for the LLM
            prompt_context = retrieve_context(query, context, session_id, user_id)
            answer = answer_question(query, session_id, user_id)

            # Extract citations
            citations = [
                {
                    "filename": chunk["metadata"]["filename"],
                    "start_row": chunk["start_row"],
                    "end_row": chunk["end_row"]
                }
                for chunk in context
            ]

            return {
                "answer": answer["content"],
                "citations": citations
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    async def create_message(self, session_id: UUID, role: str, content: str, citations: Optional[Dict], db: AsyncSession) -> Message:
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                citations=citations
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found.")
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve message: {str(e)}")

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        try:
            stmt = select(Message).where(Message.session_id == session_id)
            result = await db.execute(stmt)
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")

    async def update_message(self, message_id: UUID, content: str, db: AsyncSession) -> Message:
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found.")

            message.content = content
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found.")

            await db.delete(message)
            await db.commit()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")