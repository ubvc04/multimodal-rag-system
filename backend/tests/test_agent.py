"""Agent API tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_agent_run(async_client, auth_headers, mock_openai):
	response = await async_client.post(
		"/api/v1/agent/run",
		headers=auth_headers,
		json={"query": "Explain", "session_id": None},
	)
	assert response.status_code == 200
	assert response.json()["output"] == "agent output"


@pytest.mark.asyncio
async def test_agent_stream(async_client, auth_headers, mock_openai):
	token = auth_headers["Authorization"].split(" ")[1]
	response = await async_client.get(f"/api/v1/agent/stream?query=test&token={token}")
	assert response.status_code == 200
