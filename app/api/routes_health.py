"""Health and readiness probing endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health/live", summary="Liveness probe", status_code=status.HTTP_200_OK)
async def liveness() -> Dict[str, str]:
    """Lightweight liveness check confirming the service process is up."""
    return {
        "status": "alive",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/health/ready", summary="Readiness probe", status_code=status.HTTP_200_OK)
async def readiness(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness probe validating database connectivity and core subsystems."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "database": "connected",
            "llm_provider": settings.LLM_PROVIDER,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "service": settings.PROJECT_NAME,
                "database": f"error: {str(e)}",
            },
        )
