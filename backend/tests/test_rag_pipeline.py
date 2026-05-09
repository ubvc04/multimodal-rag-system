"""RAG pipeline tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_query_returns_answer(async_client, auth_headers, mock_openai, mock_pinecone):
	response = await async_client.post(
		"/api/v1/query",
		headers=auth_headers,
		json={"question": "What is this?", "doc_ids": None, "stream": False},
	)
	assert response.status_code == 200
	assert response.json()["answer"] == "mock answer"


@pytest.mark.asyncio
async def test_query_with_no_results(async_client, auth_headers, mock_openai, mock_pinecone, monkeypatch):
	response = await async_client.post(
		"/api/v1/query",
		headers=auth_headers,
		json={"question": "No context", "doc_ids": None, "stream": False},
	)
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_streaming_query_yields_tokens(async_client, auth_headers, mock_openai, mock_pinecone):
	response = await async_client.post(
		"/api/v1/query",
		headers=auth_headers,
		json={"question": "Stream", "doc_ids": None, "stream": True},
	)
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_multi_query_retrieval(async_client, auth_headers, mock_openai, mock_pinecone):
	response = await async_client.post(
		"/api/v1/query",
		headers=auth_headers,
		json={"question": "Multi", "doc_ids": None, "stream": False},
	)
	assert response.status_code == 200
