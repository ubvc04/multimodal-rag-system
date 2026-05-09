"""Pinecone vector store service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


@dataclass(frozen=True)
class VectorMatch:
	"""Pinecone vector match result."""

	text: str
	score: float
	metadata: dict


class VectorStoreService:
	"""Pinecone index operations."""

	def __init__(self) -> None:
		self._client = Pinecone(api_key=settings.PINECONE_API_KEY)
		index_name = settings.PINECONE_INDEX_NAME
		existing = {index["name"] for index in self._client.list_indexes()}
		if index_name not in existing:
			self._client.create_index(
				name=index_name,
				dimension=settings.PINECONE_DIMENSION,
				metric=settings.PINECONE_METRIC,
				spec=ServerlessSpec(cloud="aws", region=settings.AWS_REGION),
			)
		self._index = self._client.Index(index_name)

	async def upsert_documents(
		self,
		documents: list[Any],
		embeddings: list[list[float]],
		namespace: str,
		batch_size: int = 100,
	) -> int:
		"""Upsert embedded documents into Pinecone."""
		total = 0
		for i in range(0, len(documents), batch_size):
			batch_docs = documents[i : i + batch_size]
			batch_embeddings = embeddings[i : i + batch_size]
			vectors = []
			for doc, embedding in zip(batch_docs, batch_embeddings, strict=True):
				metadata = dict(doc.metadata)
				text = str(doc.page_content)
				metadata["text"] = text[:1000]
				vector_id = f"{metadata.get('doc_id')}:{metadata.get('chunk_index')}:{total}"
				vectors.append((vector_id, embedding, metadata))
				total += 1
			self._index.upsert(vectors=vectors, namespace=namespace)
		logger.info("pinecone_upsert", namespace=namespace, total=total)
		return total

	async def similarity_search(
		self,
		query_vector: list[float],
		namespace: str | None,
		top_k: int = 10,
		filter: dict | None = None,
		score_threshold: float = 0.7,
	) -> list[VectorMatch]:
		"""Query Pinecone and return filtered results."""
		response = self._index.query(
			vector=query_vector,
			namespace=namespace,
			top_k=top_k,
			filter=filter,
			include_metadata=True,
		)
		matches = response.get("matches", [])
		results: list[VectorMatch] = []
		for match in matches:
			score = float(match.get("score", 0))
			if score < score_threshold:
				continue
			metadata = match.get("metadata", {}) or {}
			results.append(VectorMatch(text=str(metadata.get("text", "")), score=score, metadata=metadata))
		return results

	async def delete_namespace(self, namespace: str) -> bool:
		"""Delete all vectors in a namespace."""
		self._index.delete(delete_all=True, namespace=namespace)
		return True

	@dataclass(frozen=True)
	class IndexStats:
		"""Index statistics response."""

		total_vector_count: int
		namespaces: dict
		dimension: int

	async def get_index_stats(self) -> "VectorStoreService.IndexStats":
		"""Return index statistics."""
		stats = self._index.describe_index_stats()
		return VectorStoreService.IndexStats(
			total_vector_count=int(stats.get("total_vector_count", 0)),
			namespaces=stats.get("namespaces", {}),
			dimension=int(stats.get("dimension", settings.PINECONE_DIMENSION)),
		)

	async def fetch_by_ids(self, ids: list[str], namespace: str) -> dict:
		"""Fetch vectors by their IDs."""
		return self._index.fetch(ids=ids, namespace=namespace)
