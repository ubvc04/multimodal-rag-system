"""Custom exception handlers."""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger

logger = get_logger()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
	"""Handle HTTPException with a consistent payload."""
	logger.warning("http_exception", path=str(request.url), detail=exc.detail)
	return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "status_code": exc.status_code})


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
	"""Handle request validation errors."""
	logger.warning("validation_error", path=str(request.url), errors=exc.errors())
	return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": exc.errors(), "status_code": 422})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
	"""Handle unexpected exceptions."""
	logger.exception("unhandled_exception", path=str(request.url))
	return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal server error", "status_code": 500})
