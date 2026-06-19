from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.models import UploadedFile, DocumentChunk
from backend.routers.core_application import extract_text_from_excel, chunk_text, embed_text
from ai.embeddings import get_embedding
from ai.vector_store import VectorStore
from datetime import datetime
import os


class CoreApplicationService:
    async def create_uploaded_file(
        self, session_id: UUID, filename: str, file_path: str, file_size: int, db: AsyncSession
    ) -> UploadedFile:
        try:
            uploaded_file = UploadedFile(
                id=UUID(),
                session_id=session_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                uploaded_at=datetime.utcnow(),
            )
            db.add(uploaded_file)
            await db.commit()
            await db.refresh(uploaded_file)
            return uploaded_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_uploaded_file_by_id(self, file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            uploaded_file = result.scalar_one_or_none()
            if not uploaded_file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            return uploaded_file
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_uploaded_files(self, session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_uploaded_file(self, file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            uploaded_file = result.scalar_one_or_none()
            if not uploaded_file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            await db.delete(uploaded_file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def ingest_document_chunks(self, file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            uploaded_file = await self.get_uploaded_file_by_id(file_id, db)
            file_path = uploaded_file.file_path

            # Extract text from the file
            extracted_text = extract_text_from_excel(file_path)

            # Chunk the text
            chunks = chunk_text(extracted_text, chunk_size=1000, overlap=200)

            # Embed the chunks
            embeddings = embed_text(chunks)

            # Store chunks in the database
            document_chunks = []
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    id=UUID(),
                    file_id=file_id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=index,
                    start_row=None,  # Assuming row info is not available for Excel
                    end_row=None,    # Assuming row info is not available for Excel
                    metadata={},
                    created_at=datetime.utcnow(),
                )
                db.add(document_chunk)
                document_chunks.append(document_chunk)

            await db.commit()
            return document_chunks
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during document ingestion: {str(e)}")

    async def query_documents(self, query: str, top_k: int, db: AsyncSession) -> List[DocumentChunk]:
        try:
            # Embed the query
            query_embedding = get_embedding([query])[0]

            # Perform similarity search
            vector_store = VectorStore()
            top_chunks = vector_store.search(query_embedding, top_k)

            if not top_chunks:
                raise HTTPException(status_code=404, detail="No relevant documents found")

            return top_chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during document query: {str(e)}")