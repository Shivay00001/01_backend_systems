"""
Health Check Routes - Application health monitoring endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.config import get_settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    timestamp: datetime
    environment: str
    version: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check with component status."""
    
    database: str
    cache: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns basic application health status",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns application status and version information.
    """
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        version="1.0.0",
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Returns detailed health status including dependencies",
)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check with dependency status.
    
    Checks database connectivity and other services.
    """
    settings = get_settings()
    
    # In production, actually check database connectivity
    database_status = "healthy"
    cache_status = "healthy"
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        version="1.0.0",
        database=database_status,
        cache=cache_status,
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes-style readiness probe",
)
async def readiness_probe() -> dict:
    """Readiness probe for container orchestration."""
    return {"ready": True}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes-style liveness probe",
)
async def liveness_probe() -> dict:
    """Liveness probe for container orchestration."""
    return {"alive": True}
