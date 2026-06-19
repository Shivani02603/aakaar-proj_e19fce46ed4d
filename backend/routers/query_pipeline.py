from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk, Message, UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.auth import get_current_user
from ai.embeddings import get_embedding
from ai.vector_store import VectorStore
from ai.rag import retrieve_context, answer_question

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

# Helper functions
def embed_query(query: str) -> List[float]:
    embedding = get_embedding([query])
    if not embedding or len(embedding) == 0:
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query.")
    return embedding[0]

def retrieve_top_chunks(query_embedding: List[float], top_k: int, db: Session) -> List[DocumentChunk]:
    vector_store = VectorStore(db)
    chunks = vector_store.search(query_embedding, top_k)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant chunks found.")
    return chunks

def generate_answer(query: str, context: List[str], session_id: UUID, user_id: UUID) -> dict:
    return answer_question(query=query, session_id=session_id, user_id=user_id)

# Routes
@router.post("/query", response_model=QueryResponse)
async def query_pipeline(query_request: QueryRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Handles user queries by embedding the query, retrieving relevant chunks, and generating an answer.
    """
    # Step 1: Embed the query
    query_embedding = embed_query(query_request.query)

    # Step 2: Retrieve top-k chunks
    chunks = retrieve_top_chunks(query_embedding, query_request.top_k, db)

    # Step 3: Build context from chunks
    context = [chunk.content for chunk in chunks]

    # Step 4: Generate answer using LLM
    answer_data = generate_answer(query_request.query, context, query_request.session_id, current_user["id"])

    # Step 5: Format citations
    citations = [
        {
            "filename": db.query(UploadedFile).filter(UploadedFile.id == chunk.file_id).first().filename,
            "start_row": chunk.start_row,
            "end_row": chunk.end_row,
        }
        for chunk in chunks
    ]

    return QueryResponse(answer=answer_data["answer"], citations=citations)

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieves a specific document chunk by ID.
    """
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found.")
    return DocumentChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        content=chunk.content,
        chunk_index=chunk.chunk_index,
        start_row=chunk.start_row,
        end_row=chunk.end_row,
        metadata=chunk.metadata,
    )

@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Lists all document chunks.
    """
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
        )
        for chunk in chunks
    ]

@router.delete("/chunks/{chunk_id}")
async def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Deletes a specific document chunk by ID.
    """
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found.")
    db.delete(chunk)
    db.commit()
    return {"detail": "Document chunk deleted successfully."}

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(chunk_id: UUID, chunk_update: DocumentChunkResponse, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Updates a specific document chunk by ID.
    """
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Document chunk not found.")
    for key, value in chunk_update.dict().items():
        setattr(chunk, key, value)
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
    )