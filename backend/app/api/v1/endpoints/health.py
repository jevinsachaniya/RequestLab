"""Health check and service status endpoints."""

from typing import Dict, Any
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health Check", response_model=Dict[str, Any])
def health_check() -> Dict[str, Any]:
    """Return application health, version, and current environment status.

    Useful for container orchestrators, load balancers, and uptime monitors.
    """
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

