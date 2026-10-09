"""
FastAPI Main Application.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .api.routes import router
from .document_processing.validators import DocumentValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="AI-Powered Intelligent Document Comparison System",
    description="Enterprise-grade document comparison using AI and software design patterns (Factory, Adapter, Strategy, RAG, Prompt Chaining).",
    version="1.0.0",
)

# Enable CORS for frontend Vite client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DocumentValidationError)
async def validation_exception_handler(request: Request, exc: DocumentValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": True, "code": exc.code, "message": exc.message},
    )


app.include_router(router)

# Mount static built frontend if available (supports single-service unified deployment)
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "AI Document Comparison System API is active.",
            "docs": "/docs",
            "health": "/api/health",
        }

