"""Pytest fixtures for backend tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import asyncio
import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone")
os.environ.setdefault("PINECONE_ENVIRONMENT", "us-east-1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/ragdb")

from app.core.security import get_password_hash  # noqa: E402
from app.db.init_db import create_tables, drop_tables  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.dependencies import (  # noqa: E402
	get_agent_service,
	get_document_processor,
	get_embedding_service,
	get_rag_pipeline,
	get_vector_store,
)
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.agent_service import AgentRunResult, AgentStepResult  # noqa: E402
from app.services.rag_pipeline import RAGResult, RAGSource  # noqa: E402
from app.services.vector_store import VectorMatch, VectorStoreService  # noqa: E402


def pytest_configure(config) -> None:
	"""Configure pytest asyncio mode."""
	config.option.asyncio_mode = "auto"


@pytest.fixture(scope="session")
def event_loop():
	"""Create an event loop for tests."""
	loop = asyncio.new_event_loop()
	yield loop
	loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
	"""Async client for FastAPI app."""
	transport = ASGITransport(app=app, lifespan="on")
	async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
		yield client


@pytest_asyncio.fixture(scope="session")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
	"""Create and drop test tables."""
	await create_tables()
	async with AsyncSessionLocal() as session:
		yield session
	await drop_tables()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
	"""Create a test user."""
	user = User(
		email=f"user-{uuid4()}@example.com",
		hashed_password=get_password_hash("password123"),
		full_name="Test User",
		is_active=True,
	)
	test_db.add(user)
	await test_db.commit()
	await test_db.refresh(user)
	return user


@pytest_asyncio.fixture
async def auth_headers(async_client: httpx.AsyncClient, test_user: User) -> dict:
	"""Authenticate and return auth headers."""
	response = await async_client.post(
		"/api/v1/auth/login",
		data={"username": test_user.email, "password": "password123"},
	)
	token = response.json()["access_token"]
	return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_pinecone(monkeypatch):
	"""Mock Pinecone vector store operations."""

	class MockVectorStore(VectorStoreService):
		def __init__(self) -> None:
			self._store: dict[str, list[VectorMatch]] = {}

		async def upsert_documents(self, documents, embeddings, namespace: str, batch_size: int = 100) -> int:
			matches = []
			for doc in documents:
				matches.append(VectorMatch(text=doc.page_content, score=0.9, metadata=doc.metadata))
			self._store[namespace] = matches
			return len(matches)

		async def similarity_search(self, query_vector, namespace, top_k=10, filter=None, score_threshold=0.7):
			return self._store.get(namespace or "default", [])

		async def delete_namespace(self, namespace: str) -> bool:
			self._store.pop(namespace, None)
			return True

		async def get_index_stats(self):
			return VectorStoreService.IndexStats(total_vector_count=0, namespaces={}, dimension=3)

		async def fetch_by_ids(self, ids, namespace: str):
			return {}

	monkeypatch.setattr("app.dependencies.get_vector_store", lambda: MockVectorStore())
	app.dependency_overrides[get_vector_store] = lambda: MockVectorStore()
	yield
	app.dependency_overrides.pop(get_vector_store, None)


@pytest.fixture
def mock_openai(monkeypatch):
	"""Mock OpenAI calls for deterministic responses."""

	class MockEmbeddingService:
		async def embed_documents(self, texts):
			return [[0.0, 0.0, 0.0] for _ in texts]

		async def embed_query(self, text: str):
			return [0.0, 0.0, 0.0]

		def count_tokens(self, text: str) -> int:
			return len(text.split())

		def truncate_to_token_limit(self, text: str, max_tokens: int = 8191) -> str:
			return text

	class MockDocumentProcessor:
		async def process(self, file_path: str, file_type: str, doc_id: str):
			return []

	class MockRAGPipeline:
		async def query(self, question: str, namespace=None, doc_ids=None, user_id=None):
			return RAGResult(
				answer="mock answer",
				sources=[RAGSource(text="mock", score=0.9, metadata={"doc_id": "1", "source": "file", "page": 1, "file_type": "txt", "chunk_index": 0})],
				latency_ms=10.0,
			)

		async def stream_query(self, question: str, namespace=None, doc_ids=None):
			yield "data: {\"type\": \"token\", \"data\": \"mock\"}\n\n"
			yield "data: {\"type\": \"done\", \"data\": \"\"}\n\n"

		async def multi_query_retrieval(self, question: str):
			return []

	class MockAgentService:
		async def run(self, query: str, session_id: str):
			return AgentRunResult(
				output="agent output",
				steps=[AgentStepResult(tool="document_search", input=query, output="result")],
				total_steps=1,
				session_id=session_id,
			)

		async def stream_run(self, query: str, session_id: str):
			yield "data: {\"type\": \"agent_start\", \"data\": \"start\"}\n\n"
			yield "data: {\"type\": \"done\", \"data\": \"done\"}\n\n"

	app.dependency_overrides[get_embedding_service] = lambda: MockEmbeddingService()
	app.dependency_overrides[get_document_processor] = lambda: MockDocumentProcessor()
	app.dependency_overrides[get_rag_pipeline] = lambda: MockRAGPipeline()
	app.dependency_overrides[get_agent_service] = lambda: MockAgentService()
	yield
	app.dependency_overrides.pop(get_embedding_service, None)
	app.dependency_overrides.pop(get_document_processor, None)
	app.dependency_overrides.pop(get_rag_pipeline, None)
	app.dependency_overrides.pop(get_agent_service, None)
