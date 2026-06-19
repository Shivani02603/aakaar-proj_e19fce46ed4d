from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.models import UploadedFile, DocumentChunk
from ai.embeddings import get_embedding
from ai.ingest import chunk_text, parse_excel
from ai.vector_store import VectorStore


class CoreApplicationService:
    @staticmethod
    async def create_uploaded_file(file_data: dict, db: AsyncSession) -> UploadedFile:
        try:
            new_file = UploadedFile(**file_data)
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create uploaded file: {str(e)}")

    @staticmethod
    async def get_uploaded_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")
            return file
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve uploaded file: {str(e)}")

    @staticmethod
    async def list_uploaded_files(session_id: UUID, db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.session_id == session_id))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list uploaded files: {str(e)}")

    @staticmethod
    async def delete_uploaded_file(file_id: UUID, db: AsyncSession) -> None:
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

    @staticmethod
    async def ingest_document_chunks(file_id: UUID, session_id: UUID, db: AsyncSession) -> None:
        try:
            # Retrieve the uploaded file
            file = await CoreApplicationService.get_uploaded_file_by_id(file_id, db)
            file_path = file.file_path

            # Parse the file content
            parsed_text = parse_excel(file_path)

            # Chunk the text
            chunks = chunk_text(parsed_text, chunk_size=1000, overlap=200)

            # Embed the chunks
            embeddings = get_embedding(chunks)

            # Store chunks and embeddings in the database
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                new_chunk = DocumentChunk(
                    file_id=file_id,
                    content=chunk,
                    embedding=embedding,
                    chunk_index=index,
                    metadata={"session_id": str(session_id)},
                )
                db.add(new_chunk)

            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to ingest document chunks: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error during ingestion: {str(e)}")

    @staticmethod
    async def query_documents(query: str, top_k: int, session_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            # Embed the query
            query_embedding = get_embedding([query])[0]

            # Perform vector search
            vector_store = VectorStore()
            results = vector_store.search(query_embedding, top_k=top_k)

            # Retrieve document chunks from the database
            chunk_ids = [result["id"] for result in results]
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
            chunks = result.scalars().all()

            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to query documents: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error during query: {str(e)}")