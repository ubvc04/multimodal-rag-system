"""Redis caching layer."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.config import settings


class RedisCache:
	"""Redis cache wrapper with JSON helpers."""

	def __init__(self, client: redis.Redis) -> None:
		self._client = client

	@classmethod
	def create(cls) -> "RedisCache":
		"""Create a Redis client from settings."""
		client = redis.from_url(settings.REDIS_URL, decode_responses=True)
		return cls(client)

	async def get_text(self, key: str) -> str | None:
		"""Get a string value from Redis."""
		return await self._client.get(key)

	async def set_text(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
		"""Set a string value with optional TTL."""
		await self._client.set(key, value, ex=ttl_seconds)

	async def get_json(self, key: str) -> Any | None:
		"""Get a JSON value from Redis."""
		raw = await self._client.get(key)
		if raw is None:
			return None
		return json.loads(raw)

	async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
		"""Set a JSON value with optional TTL."""
		payload = json.dumps(value)
		await self._client.set(key, payload, ex=ttl_seconds)

	async def close(self) -> None:
		"""Close the Redis connection."""
		await self._client.close()

	async def ping(self) -> bool:
		"""Ping the Redis server."""
		return bool(await self._client.ping())

	async def incr(self, key: str) -> int:
		"""Increment a key and return the new value."""
		return int(await self._client.incr(key))

	async def expire(self, key: str, ttl_seconds: int) -> None:
		"""Set a TTL on a key."""
		await self._client.expire(key, ttl_seconds)
