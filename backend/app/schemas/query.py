"""Query and agent schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
	"""Source metadata for citations."""

	doc_id: str
	source: str
	page: int | None
	file_type: str
	chunk_index: int


class SourceChunk(BaseModel):
	"""Chunk result with score and metadata."""

	text: str
	score: float
	metadata: SourceMetadata


class QueryRequest(BaseModel):
	"""Query request payload."""

	question: str = Field(..., min_length=1)
	doc_ids: list[str] | None = None
	stream: bool = False


class QueryResponse(BaseModel):
	"""Query response payload."""

	answer: str
	sources: list[SourceChunk]
	latency_ms: float


class AgentRequest(BaseModel):
	"""Agent query request payload."""

	query: str = Field(..., min_length=1)
	session_id: str | None = None


class AgentStep(BaseModel):
	"""Agent reasoning step."""

	tool: str
	input: str
	output: str


class AgentResponse(BaseModel):
	"""Agent response payload."""

	output: str
	steps: list[AgentStep]
	total_steps: int
	session_id: str


class QueryLogCreate(BaseModel):
	"""Query log entry data."""

	user_id: UUID
	document_ids: list[str] | None
	query_text: str
	response_text: str
	sources: list[dict] | None
	latency_ms: float
	token_count_input: int | None
	token_count_output: int | None
	model_used: str
	agent_used: bool
	created_at: datetime | None = None
