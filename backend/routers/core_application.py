from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, DocumentChunk, Message, Session
from database.config import get_db
from backend.services.auth import get_current_user
from backend.routers.ingestion_pipeline import parse_excel, chunk_text, embed_text
from ai.embeddings import get_embedding
from ai.rag import retrieve_context, answer_question

router = APIRouter(prefix="/api/ai", tags=["Core Application"])

# Pydantic Schemas
class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: str

class DocumentChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    content: str
    embedding: List[float]
    chunk_index: int
    start_row: int
    end_row: int
    metadata: dict
    created_at: str

class QueryRequest(BaseModel):
    query: str
    sessionId: UUID
    top_k: int = Field(default=5, ge=1)

class QueryResponse(BaseModel):
    answer: str
    citations: List[dict]

# Endpoint: Upload Excel File
@router.post("/ingest", response_model=UploadedFileResponse)
async def ingest_documents(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx files are supported.")
    
    # Save file to disk
    file_path = f"./uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Parse Excel file
    try:
        parsed_data = parse_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Excel file: {str(e)}")
    
    # Chunk data
    chunks = chunk_text(parsed_data, chunk_size=1000, overlap=200)
    
    # Embed chunks
    embeddings = embed_text(chunks)
    
    # Store chunks in database
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        document_chunk = DocumentChunk(
            file_id=None,  # Placeholder, should be linked to UploadedFile
            content=chunk,
            embedding=embedding,
            chunk_index=idx,
            start_row=0,  # Placeholder, should be calculated
            end_row=0,  # Placeholder, should be calculated
            metadata={},
            created_at=None,  # Placeholder, should be set
        )
        db.add(document_chunk)
    db.commit()
    
    # Create UploadedFile record
    uploaded_file = UploadedFile(
        session_id=session_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(parsed_data),
        uploaded_at=None,  # Placeholder, should be set
    )
    db.add(uploaded_file)
    db.commit()
    
    return UploadedFileResponse(
        id=uploaded_file.id,
        session_id=uploaded_file.session_id,
        filename=uploaded_file.filename,
        file_path=uploaded_file.file_path,
        file_size=uploaded_file.file_size,
        uploaded_at=uploaded_file.uploaded_at.isoformat(),
    )

# Endpoint: Query AI
@router.post("/query", response_model=QueryResponse)
async def ai_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Embed query
    query_embedding = get_embedding([query_request.query])[0]
    
    # Retrieve context
    context_chunks = retrieve_context(
        query=query_embedding,
        top_k=query_request.top_k,
        session_id=query_request.sessionId,
        user_id=current_user["id"],
    )
    
    # Generate answer
    try:
        answer_data = answer_question(
            query=query_request.query,
            session_id=query_request.sessionId,
            user_id=current_user["id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
    
    return QueryResponse(
        answer=answer_data["answer"],
        citations=answer_data["citations"],
    )