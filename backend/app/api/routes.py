"""
API Routes for Document Comparison and Report Generation.
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse

from ..ai.config import AIConfig
from ..comparison.service import ComparisonService
from ..document_processing.ocr import is_ocr_available
from ..document_processing.service import DocumentProcessingService
from ..document_processing.validators import DocumentValidationError
from ..models.schemas import ComparisonResponse, HealthResponse
from ..reporting.pdf_generator import generate_comparison_pdf_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# In-memory store for generated comparison results
_LATEST_COMPARISONS: Dict[str, ComparisonResponse] = {}


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Returns application health and configuration diagnostics."""
    return HealthResponse(
        status="healthy",
        ai_available=AIConfig.is_ai_configured(),
        ai_provider=AIConfig.PROVIDER,
        ocr_available=is_ocr_available(),
        supported_formats=["pdf", "docx", "txt"],
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    old_file: UploadFile = File(..., description="The baseline/original document"),
    new_file: UploadFile = File(..., description="The updated document"),
    strategy: Optional[str] = Form("semantic", description="Comparison strategy: 'semantic' or 'text'"),
) -> ComparisonResponse:
    """
    Executes end-to-end document comparison workflow:
    1. Upload & Validate
    2. Member 1: Factory & Adapter extraction (with OCR fallback) & Structuring
    3. Member 2: Matching, Strategy selection, Semantic/Text analysis, RAG, Prompt Chaining
    4. Return structured comparison response
    """
    try:
        # Read file payloads
        old_bytes = await old_file.read()
        new_bytes = await new_file.read()
        old_filename = old_file.filename or "old_document.txt"
        new_filename = new_file.filename or "new_document.txt"

        # Member 1: Document Processing Pipeline
        doc_service = DocumentProcessingService()
        old_doc = doc_service.process_file(old_filename, old_bytes)
        new_doc = doc_service.process_file(new_filename, new_bytes)

        # Member 2: Comparison Pipeline
        comparison_service = ComparisonService()
        result = comparison_service.compare_documents(
            old_doc=old_doc,
            new_doc=new_doc,
            strategy_name=strategy,
        )

        # Store latest result for quick PDF download
        _LATEST_COMPARISONS["latest"] = result

        return result

    except DocumentValidationError as ve:
        logger.warning(f"Validation error during comparison: {ve.message}")
        raise HTTPException(status_code=400, detail={"code": ve.code, "message": ve.message})
    except Exception as e:
        logger.error(f"Unexpected error processing comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": "PROCESSING_ERROR", "message": f"An error occurred while processing documents: {str(e)}"},
        )


@router.post("/report/pdf")
async def download_pdf_report(comparison_data: Optional[ComparisonResponse] = None):
    """
    Generates and returns downloadable PDF report.
    Accepts full ComparisonResponse body or retrieves the latest comparison.
    """
    target_data = comparison_data or _LATEST_COMPARISONS.get("latest")
    if not target_data:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_REPORT_DATA", "message": "No comparison data provided or available to generate PDF report."},
        )

    try:
        pdf_bytes = generate_comparison_pdf_report(target_data)
        safe_filename = f"comparison_report_{target_data.summary.old_filename}_vs_{target_data.summary.new_filename}.pdf"
        # Sanitize filename
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ("-", "_", "."))

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Content-Type": "application/pdf",
            },
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": "PDF_GENERATION_FAILED", "message": f"Failed to generate PDF report: {str(e)}"},
        )

