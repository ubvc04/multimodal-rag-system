"""Dependency injection for services."""

from __future__ import annotations

from functools import lru_cache

from app.services.agent_service import AgentService
from app.services.cache import RedisCache
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import EmbeddingService
from app.services.rag_pipeline import RAGPipeline
from app.services.vector_store import VectorStoreService


@lru_cache(maxsize=1)
def get_document_processor() -> DocumentProcessor:
	"""Return a singleton DocumentProcessor."""
	return DocumentProcessor()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
	"""Return a singleton EmbeddingService."""
	return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreService:
	"""Return a singleton VectorStoreService."""
	return VectorStoreService()


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
	"""Return a singleton RAGPipeline."""
	return RAGPipeline(get_embedding_service(), get_vector_store())


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
	"""Return a singleton AgentService."""
	return AgentService(get_rag_pipeline())


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
	"""Return a singleton RedisCache instance."""
	return RedisCache.create()
