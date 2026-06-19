from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile
from ai.embeddings import get_embedding
from ai.ingest import chunk_text
from env import CHUNK_SIZE, CHUNK_OVERLAP

class IngestionPipelineService:
    async def create_document_chunks(
        self, file_id: UUID, session_id: UUID, db: AsyncSession
    ) -> List[DocumentChunk]:
        try:
            # Fetch the uploaded file
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            uploaded_file = result.scalar_one_or_none()
            if not uploaded_file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")

            # Parse the file content
            file_path = uploaded_file.file_path
            with open(file_path, "rb") as file:
                file_content = file.read()

            # Chunk the content
            chunks = chunk_text(file_content.decode("utf-8"), CHUNK_SIZE, CHUNK_OVERLAP)

            # Embed the chunks
            embeddings = get_embedding(chunks)

            # Store chunks in the database
            document_chunks = []
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    file_id=file_id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=index,
                    metadata={"session_id": str(session_id)},
                )
                db.add(document_chunk)
                document_chunks.append(document_chunk)

            await db.commit()
            return document_chunks
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")
            return document_chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_document_chunks(self, file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            document_chunks = result.scalars().all()
            return document_chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_document_chunk(
        self, chunk_id: UUID, updated_chunk: DocumentChunk, db: AsyncSession
    ) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            # Update fields
            document_chunk.content = updated_chunk.content
            document_chunk.embedding = updated_chunk.embedding
            document_chunk.metadata = updated_chunk.metadata

            db.add(document_chunk)
            await db.commit()
            return document_chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            await db.delete(document_chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")