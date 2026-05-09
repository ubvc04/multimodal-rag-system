"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.db.init_db import create_tables
from app.db.session import async_engine
from app.dependencies import get_cache, get_vector_store
from app.services.cache import RedisCache
from app.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Manage application startup and shutdown."""
    await create_tables()
    _ = get_vector_store()
    cache = get_cache()
    app_instance.state.redis_cache = cache
    try:
        yield
    finally:
        await cache.close()
        await async_engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(v1_router, prefix="/api/v1")

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Simple health status endpoint.",
    response_description="Health payload.",
)
async def health() -> dict:
    """Return application health status."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Check DB, Redis, and Pinecone availability.",
    response_description="Readiness status.",
)
async def readiness(request: Request) -> dict:
    """Check readiness dependencies."""
    cache: RedisCache = request.app.state.redis_cache
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await cache.ping()
        _ = await get_vector_store().get_index_stats()
    except Exception as exc:
        logger.exception("readiness_failed")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {"status": "ready"}
