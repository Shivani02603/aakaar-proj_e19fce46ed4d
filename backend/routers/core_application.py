from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from database.models import UploadedFile, DocumentChunk, User
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.core_application_service import CoreApplicationService
from backend.services.query_pipeline_service import QueryPipelineService
from backend.services.upload_service import UploadService
from backend.services.ingestion_pipeline_service import create_document_chunks
from backend.services.query_pipeline_service import retrieve_chunks, build_prompt, call_llm
from backend.services.core_application_service import extract_text_from_excel, ingest_excel

router = APIRouter(prefix="/core_application", tags=["Core Application"])

# Pydantic schemas
class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime

class QueryRequest(BaseModel):
    query: str
    session_id: UUID
    top_k: int = Field(default=5, ge=1)

class QueryResponse(BaseModel):
    answer: str
    citations: List[dict]

# Upload Excel file endpoint
@router.post("/upload", response_model=UploadedFileResponse)
async def upload_excel_file(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")
    
    upload_service = UploadService()
    uploaded_file = await upload_service.upload_file(session_id=session_id, file=file, db=db)
    
    return UploadedFileResponse(
        id=uploaded_file.id,
        session_id=uploaded_file.session_id,
        filename=uploaded_file.filename,
        file_path=uploaded_file.file_path,
        file_size=uploaded_file.file_size,
        uploaded_at=uploaded_file.uploaded_at,
    )

# Query data endpoint
@router.post("/query", response_model=QueryResponse)
async def query_data(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retrieve relevant chunks based on the query
    query_pipeline_service = QueryPipelineService()
    query_embedding = query_pipeline_service.embed_query(query_request.query)
    chunks = retrieve_chunks(query_embedding=query_embedding, top_k=query_request.top_k, db=db)
    
    # Build the prompt and call the LLM
    prompt = build_prompt(chunks=chunks, query=query_request.query)
    llm_response = call_llm(messages=[{"role": "user", "content": prompt}], stream=False)
    
    return QueryResponse(answer=llm_response["answer"], citations=llm_response["citations"])

# List uploaded files endpoint
@router.get("/files", response_model=List[UploadedFileResponse])
async def list_uploaded_files(
    session_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    core_service = CoreApplicationService()
    uploaded_files = core_service.list_uploaded_files(session_id=session_id, db=db)
    
    return [
        UploadedFileResponse(
            id=file.id,
            session_id=file.session_id,
            filename=file.filename,
            file_path=file.file_path,
            file_size=file.file_size,
            uploaded_at=file.uploaded_at,
        )
        for file in uploaded_files
    ]

# Get uploaded file by ID endpoint
@router.get("/files/{file_id}", response_model=UploadedFileResponse)
async def get_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    core_service = CoreApplicationService()
    uploaded_file = core_service.get_uploaded_file_by_id(file_id=file_id, db=db)
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found.")
    
    return UploadedFileResponse(
        id=uploaded_file.id,
        session_id=uploaded_file.session_id,
        filename=uploaded_file.filename,
        file_path=uploaded_file.file_path,
        file_size=uploaded_file.file_size,
        uploaded_at=uploaded_file.uploaded_at,
    )

# Delete uploaded file endpoint
@router.delete("/files/{file_id}")
async def delete_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    core_service = CoreApplicationService()
    core_service.delete_uploaded_file(file_id=file_id, db=db)
    return {"detail": "File deleted successfully."}

# Ingest Excel file endpoint
@router.post("/ingest")
async def ingest_excel_file(
    file_id: UUID = Form(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    core_service = CoreApplicationService()
    uploaded_file = core_service.get_uploaded_file_by_id(file_id=file_id, db=db)
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Extract text and ingest document chunks
    extracted_text = extract_text_from_excel(file_path=uploaded_file.file_path)
    document_chunks = await create_document_chunks(file_id=file_id, session=db)
    
    return {"detail": "File ingested successfully.", "chunks_created": len(document_chunks)}