"""Custom middleware implementations."""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.services.cache import RedisCache
from app.utils.logger import get_logger

logger = get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
	"""Log incoming requests with latency."""

	async def dispatch(self, request: Request, call_next) -> Response:
		"""Log request details and latency."""
		start = time.perf_counter()
		request_id = str(uuid4())
		request.state.request_id = request_id

		response: Response = await call_next(request)

		latency_ms = (time.perf_counter() - start) * 1000
		logger.info(
			"request",
			method=request.method,
			path=request.url.path,
			status_code=response.status_code,
			latency_ms=round(latency_ms, 2),
			request_id=request_id,
			user_agent=request.headers.get("user-agent", ""),
		)

		response.headers["X-Request-ID"] = request_id
		response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
		return response


class RateLimitMiddleware(BaseHTTPMiddleware):
	"""Simple Redis-backed rate limiting middleware."""

	async def dispatch(self, request: Request, call_next) -> Response:
		"""Enforce request rate limits per client IP."""
		if request.url.path in {"/health", "/ready", "/metrics", "/docs", "/openapi.json"}:
			return await call_next(request)

		cache: RedisCache | None = getattr(request.app.state, "redis_cache", None)
		if cache is None:
			return await call_next(request)

		window = settings.RATE_LIMIT_WINDOW_SECONDS
		limit = settings.RATE_LIMIT_REQUESTS
		ip = request.headers.get("x-forwarded-for")
		client_ip = ip.split(",")[0].strip() if ip else (request.client.host if request.client else "unknown")
		window_key = int(time.time() // window)
		key = f"rate_limit:{client_ip}:{window_key}"

		count = await cache.incr(key)
		if count == 1:
			await cache.expire(key, window)

		remaining = max(0, limit - int(count))
		reset = (window_key + 1) * window

		if int(count) > limit:
			response = Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content="Rate limit exceeded")
			response.headers["Retry-After"] = str(reset - int(time.time()))
			response.headers["X-RateLimit-Limit"] = str(limit)
			response.headers["X-RateLimit-Remaining"] = "0"
			response.headers["X-RateLimit-Reset"] = str(reset)
			return response

		response = await call_next(request)
		response.headers["X-RateLimit-Limit"] = str(limit)
		response.headers["X-RateLimit-Remaining"] = str(remaining)
		response.headers["X-RateLimit-Reset"] = str(reset)
		return response
