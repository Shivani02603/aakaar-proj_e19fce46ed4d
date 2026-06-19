from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ai.ingest import ingest
from ai.rag import answer

router = APIRouter(prefix="/api/ai")

# Request model for ingestion
class IngestRequest(BaseModel):
    file_path: str

# Response model for ingestion
class IngestResponse(BaseModel):
    success: bool
    message: str

# Request model for query
class QueryRequest(BaseModel):
    question: str

# Response model for query
class QueryResponse(BaseModel):
    answer: str
    citations: List[dict]

@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(request: IngestRequest):
    try:
        success, message = ingest(request.file_path)
        return IngestResponse(success=success, message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        answer_text, citations = answer(request.question)
        return QueryResponse(answer=answer_text, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))