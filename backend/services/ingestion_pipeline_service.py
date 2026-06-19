from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile
from backend.routers.core_application import chunk_text, embed_text
from backend.models import DocumentChunk as DocumentChunkModel
from datetime import datetime
import pandas as pd
import os

class IngestionPipelineService:
    async def create_document_chunks(self, file_id: UUID, session: AsyncSession) -> List[DocumentChunk]:
        try:
            # Fetch the uploaded file details
            result = await session.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            uploaded_file = result.scalar_one_or_none()
            if not uploaded_file:
                raise HTTPException(status_code=404, detail="Uploaded file not found")

            # Parse the Excel file
            file_path = uploaded_file.file_path
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File path does not exist")

            excel_data = pd.ExcelFile(file_path)
            all_chunks = []

            for sheet_name in excel_data.sheet_names:
                sheet_data = excel_data.parse(sheet_name)
                text_data = sheet_data.to_string(index=False, header=False)

                # Chunk the text data
                chunks = chunk_text(text_data, chunk_size=1000, overlap=200)

                # Embed the chunks
                embeddings = embed_text(chunks)

                # Store chunks in the database
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    document_chunk = DocumentChunkModel(
                        id=UUID(),
                        file_id=file_id,
                        content=chunk,
                        embedding=embedding,
                        chunk_index=index,
                        start_row=None,  # Optional: Define based on your chunking logic
                        end_row=None,    # Optional: Define based on your chunking logic
                        metadata={"sheet_name": sheet_name},
                        created_at=datetime.utcnow()
                    )
                    session.add(document_chunk)
                    all_chunks.append(document_chunk)

            await session.commit()
            return all_chunks
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    async def get_document_chunk_by_id(self, chunk_id: UUID, session: AsyncSession) -> DocumentChunk:
        try:
            result = await session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")
            return document_chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_document_chunks(self, file_id: UUID, session: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await session.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            document_chunks = result.scalars().all()
            return document_chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_document_chunk(self, chunk_id: UUID, updated_data: dict, session: AsyncSession) -> DocumentChunk:
        try:
            result = await session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            for key, value in updated_data.items():
                if hasattr(document_chunk, key):
                    setattr(document_chunk, key, value)

            await session.commit()
            return document_chunk
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_document_chunk(self, chunk_id: UUID, session: AsyncSession) -> None:
        try:
            result = await session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            document_chunk = result.scalar_one_or_none()
            if not document_chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            await session.delete(document_chunk)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")