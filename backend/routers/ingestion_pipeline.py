from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
from openai import Embedding
from database.models import DocumentChunk, UploadedFile
from database.config import get_db
from backend.services.auth import get_current_user
from backend.routers.core_application import chunk_text, embed_text

router = APIRouter(prefix="/ingestion_pipeline", tags=["Ingestion Pipeline"])

# Pydantic schemas
class DocumentChunkCreate(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: Optional[dict] = None

class DocumentChunkResponse(DocumentChunkCreate):
    id: UUID
    created_at: datetime

class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

# Helper functions
def parse_excel(file_path: str) -> List[str]:
    try:
        df = pd.read_excel(file_path, sheet_name=None)
        content = []
        for sheet_name, sheet_data in df.items():
            content.append(sheet_data.to_string(index=False, header=False))
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")

def store_chunks(chunks: List[DocumentChunkCreate], db: Session):
    try:
        for chunk in chunks:
            db_chunk = DocumentChunk(
                file_id=chunk.file_id,
                content=chunk.content,
                embedding=chunk.embedding,
                chunk_index=chunk.chunk_index,
                start_row=chunk.start_row,
                end_row=chunk.end_row,
                metadata=chunk.metadata,
                created_at=datetime.utcnow(),
            )
            db.add(db_chunk)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error storing chunks: {str(e)}")

# Routes
@router.post("/ingest", response_model=UploadedFileResponse)
async def ingest_documents(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Ingest an Excel file, parse its content, chunk it, embed the chunks, and store them in the database.
    """
    try:
        # Save the uploaded file
        file_path = f"./uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Create UploadedFile entry
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(file.file.read()),
            uploaded_at=datetime.utcnow(),
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)

        # Parse Excel content
        content = parse_excel(file_path)

        # Chunk the content
        chunks = []
        for sheet_content in content:
            chunked_texts = chunk_text(sheet_content, chunk_size=1000, overlap=200)
            embeddings = embed_text(chunked_texts)
            for idx, (text, embedding) in enumerate(zip(chunked_texts, embeddings)):
                chunks.append(
                    DocumentChunkCreate(
                        file_id=uploaded_file.id,
                        content=text,
                        embedding=embedding,
                        chunk_index=idx,
                        start_row=0,  # Placeholder, adjust based on actual parsing logic
                        end_row=0,  # Placeholder, adjust based on actual parsing logic
                        metadata={"sheet_name": file.filename},
                    )
                )

        # Store chunks in the database
        store_chunks(chunks, db)

        return UploadedFileResponse(
            id=uploaded_file.id,
            session_id=uploaded_file.session_id,
            filename=uploaded_file.filename,
            file_path=uploaded_file.file_path,
            file_size=uploaded_file.file_size,
            uploaded_at=uploaded_file.uploaded_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")

@router.get("/chunks/{file_id}", response_model=List[DocumentChunkResponse])
async def list_document_chunks(file_id: UUID, db: Session = Depends(get_db)):
    """
    List all document chunks for a given file ID.
    """
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).all()
        return [
            DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                content=chunk.content,
                embedding=chunk.embedding,
                chunk_index=chunk.chunk_index,
                start_row=chunk.start_row,
                end_row=chunk.end_row,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing document chunks: {str(e)}")

@router.delete("/chunks/{chunk_id}")
async def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a document chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found")
        db.delete(chunk)
        db.commit()
        return {"message": "Document chunk deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document chunk: {str(e)}")