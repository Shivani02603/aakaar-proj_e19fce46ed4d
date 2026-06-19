from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
from contextlib import asynccontextmanager
from database.config import init_db
from backend.routers.sessions import router as sessions_router
from backend.routers.upload import router as upload_router
from ai.routes import router as ai_router

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="AI-powered web application for document processing and Q&A.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # Allow localhost and all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers with /api prefix
app.include_router(sessions_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# Global exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # Initialize the database
    yield
    # Perform any necessary cleanup here

app.router.lifespan_context = lifespan