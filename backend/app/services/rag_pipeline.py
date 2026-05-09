"""RAG pipeline implementation."""

from __future__ import annotations

import hashlib
import time
from collections.abc import AsyncGenerator
from typing import Any

from dataclasses import dataclass

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever

from app.config import settings
from app.services.embeddings import EmbeddingService
from app.services.streaming import sse_event
from app.services.vector_store import VectorMatch, VectorStoreService


class _PineconeRetriever(BaseRetriever):
	"""Custom retriever bridging Pinecone with LangChain."""

	def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStoreService) -> None:
		super().__init__()
		self._embedding_service = embedding_service
		self._vector_store = vector_store

	async def _aget_relevant_documents(self, query: str) -> list[Document]:
		vector = await self._embedding_service.embed_query(query)
		results = await self._vector_store.similarity_search(vector, namespace=None, top_k=settings.PINECONE_TOP_K)
		docs: list[Document] = []
		for item in results:
			docs.append(Document(page_content=item["text"], metadata=item["metadata"]))
		return docs

	def _get_relevant_documents(self, query: str) -> list[Document]:
		raise NotImplementedError("Sync retrieval not supported")


@dataclass(frozen=True)
class RAGSource:
	"""Source citation with metadata."""

	text: str
	score: float
	metadata: dict


@dataclass(frozen=True)
class RAGResult:
	"""RAG response result."""

	answer: str
	sources: list[RAGSource]
	latency_ms: float


class RAGPipeline:
	"""RAG pipeline orchestrating retrieval and generation."""

	def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStoreService) -> None:
		self.embedding_service = embedding_service
		self.vector_store = vector_store
		self.llm = ChatOpenAI(
			model=settings.OPENAI_CHAT_MODEL,
			temperature=settings.OPENAI_TEMPERATURE,
			max_tokens=settings.OPENAI_MAX_TOKENS,
			streaming=True,
			callbacks=[StreamingStdOutCallbackHandler()],
		)
		self.prompt = self._build_prompt()

	def _build_prompt(self) -> ChatPromptTemplate:
		system_message = (
			"You are an expert AI assistant with access to a knowledge base. "
			"Answer questions based ONLY on the provided context. "
			"If the context doesn't contain enough information, say so clearly. "
			"Always cite your sources by referencing the document name and page number. "
			"Format your response in clear, structured markdown."
		)
		human_message = "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
		return ChatPromptTemplate.from_messages([("system", system_message), ("human", human_message)])

	def _format_context(self, retrieved_docs: list[VectorMatch]) -> tuple[str, list[RAGSource]]:
		formatted = []
		sources: list[RAGSource] = []
		for idx, doc in enumerate(retrieved_docs, start=1):
			metadata = doc.metadata
			source = metadata.get("source", "unknown")
			page = metadata.get("page")
			text = doc.text
			formatted.append(f"[Source {idx}] {source}, Page {page}\n{text}\n")
			sources.append(RAGSource(text=text, score=doc.score, metadata=metadata))
		return "\n".join(formatted), sources

	async def query(
		self,
		question: str,
		namespace: str | None = None,
		doc_ids: list[str] | None = None,
		user_id: str | None = None,
	) -> RAGResult:
		"""Run a non-streaming RAG query and return the result."""
		start = time.perf_counter()
		query_vector = await self.embedding_service.embed_query(question)
		metadata_filter = {"doc_id": {"$in": doc_ids}} if doc_ids else None
		retrieved = await self.vector_store.similarity_search(
			query_vector,
			namespace=namespace,
			top_k=settings.PINECONE_TOP_K,
			filter=metadata_filter,
		)
		context, sources = self._format_context(retrieved)
		chain = self.prompt | self.llm | StrOutputParser()
		answer = await chain.ainvoke({"question": question, "context": context})
		latency_ms = (time.perf_counter() - start) * 1000
		return RAGResult(answer=answer, sources=sources, latency_ms=latency_ms)

	async def stream_query(
		self,
		question: str,
		namespace: str | None = None,
		doc_ids: list[str] | None = None,
	) -> AsyncGenerator[str, None]:
		"""Stream a RAG query as SSE events."""
		try:
			query_vector = await self.embedding_service.embed_query(question)
			metadata_filter = {"doc_id": {"$in": doc_ids}} if doc_ids else None
			retrieved = await self.vector_store.similarity_search(
				query_vector,
				namespace=namespace,
				top_k=settings.PINECONE_TOP_K,
				filter=metadata_filter,
			)
			context, sources = self._format_context(retrieved)
			yield sse_event({"type": "sources", "data": [source.__dict__ for source in sources]})

			chain = self.prompt | self.llm | StrOutputParser()
			async for token in chain.astream({"question": question, "context": context}):
				yield sse_event({"type": "token", "data": token})

			yield sse_event({"type": "done", "data": ""})
		except Exception as exc:
			yield sse_event({"type": "error", "data": str(exc)})

	async def multi_query_retrieval(self, question: str) -> list[VectorMatch]:
		"""Retrieve documents using multiple query variations."""
		retriever = _PineconeRetriever(self.embedding_service, self.vector_store)
		multi_retriever = MultiQueryRetriever.from_llm(
			retriever=retriever,
			llm=self.llm,
			include_original=True,
		)
		docs = await multi_retriever.aget_relevant_documents(question)
		seen: set[str] = set()
		merged: list[VectorMatch] = []
		for doc in docs:
			digest = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
			if digest in seen:
				continue
			seen.add(digest)
			merged.append(
				VectorMatch(
					text=doc.page_content,
					metadata=doc.metadata,
					score=float(doc.metadata.get("score", 0.0)),
				)
			)
		return merged
