from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk, UploadedFile
from database.config import get_db
from backend.services.query_pipeline_service import embed_query, retrieve_top_chunks, generate_answer
from backend.services.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/query_pipeline", tags=["Query Pipeline"])

# Pydantic schemas
class QueryRequest(BaseModel):
    query: str
    session_id: UUID
    top_k: int = Field(default=5, ge=1, le=10)

class QueryResponse(BaseModel):
    answer: str
    citations: List[dict]

class DocumentChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict
    created_at: str

# Endpoint to query the pipeline
@router.post("/query", response_model=QueryResponse)
async def query_pipeline(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handles user queries by embedding the query, retrieving relevant chunks,
    and generating an answer using the context.
    """
    try:
        # Embed the query
        query_embedding = embed_query(query_request.query)

        # Retrieve top-k chunks based on cosine similarity
        chunks = retrieve_top_chunks(query_embedding, query_request.top_k, db)

        # Generate the answer using the retrieved context
        answer, citations = generate_answer(query_request.query, chunks)

        return QueryResponse(answer=answer, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# Endpoint to list all document chunks
@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all document chunks available in the database.
    """
    try:
        chunks = db.query(DocumentChunk).all()
        return [
            DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                start_row=chunk.start_row,
                end_row=chunk.end_row,
                metadata=chunk.metadata,
                created_at=chunk.created_at.isoformat(),
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document chunks: {str(e)}")

# Endpoint to retrieve a specific document chunk by ID
@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a specific document chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found")
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            start_row=chunk.start_row,
            end_row=chunk.end_row,
            metadata=chunk.metadata,
            created_at=chunk.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document chunk: {str(e)}")

# Endpoint to delete a document chunk by ID
@router.delete("/chunks/{chunk_id}")
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a specific document chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found")
        db.delete(chunk)
        db.commit()
        return {"detail": "Document chunk deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document chunk: {str(e)}")

# Endpoint to update a document chunk by ID
@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(
    chunk_id: UUID,
    updated_data: DocumentChunkResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates a specific document chunk by its ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found")
        
        chunk.content = updated_data.content
        chunk.chunk_index = updated_data.chunk_index
        chunk.start_row = updated_data.start_row
        chunk.end_row = updated_data.end_row
        chunk.metadata = updated_data.metadata
        db.commit()
        db.refresh(chunk)
        
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            start_row=chunk.start_row,
            end_row=chunk.end_row,
            metadata=chunk.metadata,
            created_at=chunk.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document chunk: {str(e)}")