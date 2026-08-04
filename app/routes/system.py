from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.llm_service import llm_service
from config.settings import settings

router = APIRouter(tags=["System"])


@router.get(
    "/",
    summary="Root endpoint",
    description="Basic project info"
)
def root():
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "env": settings.APP_ENV,
        "docs": "/docs"
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API keys status and system health"
)
def health_check():
    return HealthResponse(
        status="healthy" if settings.is_ready() else "degraded",
        api_keys=settings.validate_keys(),
        model=llm_service.model_name,
        version=settings.APP_VERSION,
    )