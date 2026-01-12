"""Health check route."""

from fastapi import APIRouter

from ..schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status and version
    Invoked by: (no references found)
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
    )
