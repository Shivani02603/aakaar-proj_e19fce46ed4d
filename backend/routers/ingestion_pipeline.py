from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.routers.ingestion_pipeline import chunk_text, embed_text
from ai.embeddings import get_embedding
from ai.vector_store import VectorStore
from datetime import datetime
import os
import pandas as pd
import tempfile

router = APIRouter(prefix="/ingestion_pipeline", tags=["Ingestion Pipeline"])

# Pydantic Schemas
class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

class DocumentChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict
    created_at: datetime

class IngestRequest(BaseModel):
    session_id: UUID
    file_id: UUID

class IngestResponse(BaseModel):
    success: bool
    message: str

# Helper Functions
def parse_excel(file_path: str) -> List[str]:
    try:
        df = pd.read_excel(file_path, sheet_name=None)  # Parse all sheets
        content = []
        for sheet_name, sheet_data in df.items():
            content.append(sheet_data.to_string(index=False))
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {str(e)}")

def store_chunks(chunks: List[str], embeddings: List[List[float]], file_id: UUID, db: Session):
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        document_chunk = DocumentChunk(
            file_id=file_id,
            content=chunk,
            embedding=embedding,
            chunk_index=index,
            start_row=0,  # Placeholder for row-based metadata
            end_row=0,    # Placeholder for row-based metadata
            metadata={},
            created_at=datetime.utcnow()
        )
        db.add(document_chunk)
    db.commit()

# Routes
@router.post("/upload", response_model=UploadedFileResponse)
async def upload_excel_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name

        # Create UploadedFile record
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=file.filename,
            file_path=temp_file_path,
            file_size=os.path.getsize(temp_file_path),
            uploaded_at=datetime.utcnow()
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)

        return UploadedFileResponse(
            id=uploaded_file.id,
            session_id=uploaded_file.session_id,
            filename=uploaded_file.filename,
            file_path=uploaded_file.file_path,
            file_size=uploaded_file.file_size,
            uploaded_at=uploaded_file.uploaded_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    ingest_request: IngestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Retrieve file record
        file_record = db.query(UploadedFile).filter(UploadedFile.id == ingest_request.file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        # Parse Excel file
        content = parse_excel(file_record.file_path)

        # Chunk content
        chunks = chunk_text(content, chunk_size=1000, overlap=200)

        # Embed chunks
        embeddings = embed_text(chunks)

        # Store chunks and embeddings
        store_chunks(chunks, embeddings, file_record.id, db)

        return IngestResponse(success=True, message="Document ingestion completed successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest documents: {str(e)}")

@router.get("/chunks/{file_id}", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
                created_at=chunk.created_at
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document chunks: {str(e)}")

@router.delete("/chunks/{chunk_id}", response_model=dict)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        db.delete(chunk)
        db.commit()
        return {"success": True, "message": "Document chunk deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document chunk: {str(e)}")