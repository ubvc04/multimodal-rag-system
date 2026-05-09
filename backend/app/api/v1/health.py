"""Health endpoints for API v1."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
	"",
	status_code=status.HTTP_200_OK,
	summary="Health check",
	description="Return API health status.",
	response_description="Health status payload.",
)
async def health_check() -> dict:
	"""Return API health status."""
	return {"status": "ok", "version": settings.APP_VERSION}
