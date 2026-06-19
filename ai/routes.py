from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from ai.ingest import ingest
from ai.rag import answer

router = APIRouter(prefix="/api/ai")

# Request model for the /ingest endpoint
class IngestRequest(BaseModel):
    file_path: str

# Response model for the /ingest endpoint
class IngestResponse(BaseModel):
    success: bool
    message: str

# Request model for the /query endpoint
class QueryRequest(BaseModel):
    question: str

# Response model for the /query endpoint
class QueryResponse(BaseModel):
    answer: str
    citations: List[dict]

@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(request: IngestRequest):
    try:
        result = await ingest(request.file_path)
        return IngestResponse(success=True, message=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        result = await answer(request.question)
        return QueryResponse(answer=result["answer"], citations=result["citations"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))