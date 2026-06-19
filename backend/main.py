from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from database.config import init_db
from backend.routes.sessions import router as sessions_router
from backend.routes.upload import router as upload_router
from ai.routes import router as ai_router

app = FastAPI(
    title="Aakaar Project",
    description="AI-powered web application backend",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(sessions_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# Lifespan context manager
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    pass  # Add any shutdown logic if needed

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return {
        "error": "Validation error",
        "details": exc.errors(),
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return {
        "error": "Internal server error",
        "details": str(exc),
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }