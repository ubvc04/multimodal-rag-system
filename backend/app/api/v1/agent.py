"""Agentic reasoning routes."""

from __future__ import annotations

from typing import AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_token, get_current_active_user
from app.db.session import get_db
from app.dependencies import get_agent_service
from app.models.query_log import QueryLog
from app.models.user import User
from app.schemas.query import AgentRequest, AgentResponse, AgentStep
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
	"/run",
	response_model=AgentResponse,
	status_code=status.HTTP_200_OK,
	summary="Run the agent",
	description="Run the agent with tool execution.",
	response_description="Agent output with steps.",
)
async def run_agent(
	request: AgentRequest,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
	agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
	"""Run the agent and return output with steps."""
	session_id = request.session_id or str(uuid4())
	result = await agent_service.run(request.query, session_id)
	steps = [AgentStep(tool=step.tool, input=step.input, output=step.output) for step in result.steps]

	log = QueryLog(
		user_id=current_user.id,
		document_ids=None,
		query_text=request.query,
		response_text=result.output,
		sources=None,
		latency_ms=0.0,
		token_count_input=None,
		token_count_output=None,
		model_used=settings.OPENAI_CHAT_MODEL,
		agent_used=True,
	)
	db.add(log)

	return AgentResponse(output=result.output, steps=steps, total_steps=result.total_steps, session_id=session_id)


@router.get(
	"/stream",
	status_code=status.HTTP_200_OK,
	summary="Stream agent reasoning",
	description="Stream agent reasoning steps over SSE.",
	response_description="Streaming response.",
)
async def stream_agent(
	query: str = Query(..., min_length=1),
	token: str | None = None,
	session_id: str | None = None,
	agent_service: AgentService = Depends(get_agent_service),
) -> EventSourceResponse:
	"""Stream agent events via SSE."""
	if not token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
	payload = decode_token(token)
	if payload["type"] != "access":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

	session = session_id or str(uuid4())

	async def event_generator() -> AsyncGenerator[str, None]:
		async for event in agent_service.stream_run(query, session):
			yield event

	headers = {
		"Cache-Control": "no-cache",
		"X-Accel-Buffering": "no",
	}
	return EventSourceResponse(event_generator(), headers=headers)
