"""RAG query routes."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_token, get_current_active_user
from app.db.session import get_db
from app.dependencies import get_rag_pipeline
from app.models.query_log import QueryLog
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse, SourceChunk, SourceMetadata
from app.services.rag_pipeline import RAGPipeline
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
	"",
	response_model=QueryResponse,
	status_code=status.HTTP_200_OK,
	summary="Run a RAG query",
	description="Run a retrieval-augmented query with optional streaming.",
	response_description="Answer with citations.",
)
async def query_documents(
	request: QueryRequest,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
	rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> QueryResponse:
	"""Execute a RAG query and return the response."""
	if request.stream:
		async def event_generator() -> AsyncGenerator[str, None]:
			async for event in rag_pipeline.stream_query(question=request.question, doc_ids=request.doc_ids):
				yield event

		return StreamingResponse(event_generator(), media_type="text/event-stream")

	result = await rag_pipeline.query(question=request.question, doc_ids=request.doc_ids, user_id=str(current_user.id))
	sources = [
		SourceChunk(
			text=src.text,
			score=float(src.score),
			metadata=SourceMetadata(
				doc_id=str(src.metadata.get("doc_id")),
				source=str(src.metadata.get("source")),
				page=src.metadata.get("page"),
				file_type=str(src.metadata.get("file_type", "")),
				chunk_index=int(src.metadata.get("chunk_index", 0)),
			),
		)
		for src in result.sources
	]

	log = QueryLog(
		user_id=current_user.id,
		document_ids=request.doc_ids,
		query_text=request.question,
		response_text=result.answer,
		sources=[source.__dict__ for source in result.sources],
		latency_ms=result.latency_ms,
		token_count_input=None,
		token_count_output=None,
		model_used=settings.OPENAI_CHAT_MODEL,
		agent_used=False,
	)
	db.add(log)

	return QueryResponse(answer=result.answer, sources=sources, latency_ms=result.latency_ms)


@router.get(
	"/stream",
	status_code=status.HTTP_200_OK,
	summary="Stream a RAG query",
	description="Stream retrieval-augmented responses using SSE.",
	response_description="Streaming response.",
)
async def stream_query(
	question: str = Query(..., min_length=1),
	doc_ids: str | None = None,
	token: str | None = None,
	rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> EventSourceResponse:
	"""Stream a RAG query via SSE."""
	if not token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
	payload = decode_token(token)
	if payload["type"] != "access":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

	doc_id_list = [doc_id.strip() for doc_id in doc_ids.split(",")] if doc_ids else None

	async def event_generator() -> AsyncGenerator[str, None]:
		async for event in rag_pipeline.stream_query(question=question, doc_ids=doc_id_list):
			yield event

	headers = {
		"Cache-Control": "no-cache",
		"X-Accel-Buffering": "no",
	}
	return EventSourceResponse(event_generator(), headers=headers)
