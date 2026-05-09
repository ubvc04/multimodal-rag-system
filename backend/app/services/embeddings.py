"""Embedding service using OpenAI."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import tiktoken
from langchain_openai import OpenAIEmbeddings
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.cache import RedisCache
from app.utils.logger import get_logger

logger = get_logger()


class EmbeddingService:
	"""OpenAI embedding service with caching and token tracking."""

	def __init__(self) -> None:
		self._embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)
		self._encoder = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
		self._cache = RedisCache.create()

	async def embed_documents(self, texts: list[str]) -> list[list[float]]:
		"""Embed a list of documents in batches with retries."""
		batch_size = 100
		embeddings: list[list[float]] = []
		for idx in range(0, len(texts), batch_size):
			batch = texts[idx : idx + batch_size]
			async for attempt in AsyncRetrying(
				stop=stop_after_attempt(3),
				wait=wait_exponential(multiplier=1, min=1, max=8),
				retry=retry_if_exception_type(Exception),
				reraise=True,
			):
				with attempt:
					batch_embeddings = await self._embeddings.aembed_documents(batch)
					embeddings.extend(batch_embeddings)
					token_count = sum(self.count_tokens(text) for text in batch)
					logger.info("embedding_batch", batch_size=len(batch), token_count=token_count)
			await asyncio.sleep(0)
		return embeddings

	async def embed_query(self, text: str) -> list[float]:
		"""Embed a query string with caching."""
		cache_key = self._hash_text(text)
		cached = await self._cache.get_json(cache_key)
		if isinstance(cached, list):
			return [float(x) for x in cached]

		embedding = await self._embeddings.aembed_query(text)
		await self._cache.set_json(cache_key, embedding, ttl_seconds=settings.CACHE_TTL_SECONDS)
		logger.info("embedding_query", token_count=self.count_tokens(text))
		return embedding

	def count_tokens(self, text: str) -> int:
		"""Count tokens for the embedding model."""
		return len(self._encoder.encode(text))

	def truncate_to_token_limit(self, text: str, max_tokens: int = 8191) -> str:
		"""Truncate text to the max token limit for the model."""
		tokens = self._encoder.encode(text)
		truncated = tokens[:max_tokens]
		return self._encoder.decode(truncated)

	@staticmethod
	def _hash_text(text: str) -> str:
		"""Hash text to a stable cache key."""
		return hashlib.sha256(text.encode("utf-8")).hexdigest()
