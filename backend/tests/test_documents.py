"""Document API tests."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.config import settings
from app.models.document import Document, DocumentStatus


@pytest.mark.asyncio
async def test_upload_pdf_success(async_client, auth_headers, mock_openai, mock_pinecone):
	file_content = b"%PDF-1.4 test pdf"
	files = {"file": ("test.pdf", file_content, "application/pdf")}
	response = await async_client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
	assert response.status_code == 202
	assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_upload_file_too_large(async_client, auth_headers, mock_openai, mock_pinecone, monkeypatch):
	monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0)
	files = {"file": ("test.txt", b"hello", "text/plain")}
	response = await async_client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
	assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_invalid_type(async_client, auth_headers, mock_openai, mock_pinecone):
	files = {"file": ("test.exe", b"data", "application/octet-stream")}
	response = await async_client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
	assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_documents(async_client, auth_headers, test_db: AsyncSession, test_user):
	doc = Document(
		user_id=test_user.id,
		filename="file.txt",
		original_filename="file.txt",
		file_type="txt",
		file_size_bytes=10,
		status=DocumentStatus.INDEXED,
		pinecone_namespace="ns",
		chunk_count=1,
	)
	test_db.add(doc)
	await test_db.commit()

	response = await async_client.get("/api/v1/documents", headers=auth_headers)
	assert response.status_code == 200
	assert response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_delete_document(async_client, auth_headers, test_db: AsyncSession, test_user, mock_pinecone):
	doc = Document(
		user_id=test_user.id,
		filename="file.txt",
		original_filename="file.txt",
		file_type="txt",
		file_size_bytes=10,
		status=DocumentStatus.INDEXED,
		pinecone_namespace="ns-delete",
		chunk_count=1,
	)
	test_db.add(doc)
	await test_db.commit()
	await test_db.refresh(doc)

	response = await async_client.delete(f"/api/v1/documents/{doc.id}", headers=auth_headers)
	assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_users_document(async_client, auth_headers, test_db: AsyncSession):
	other_doc = Document(
		user_id=uuid4(),
		filename="other.txt",
		original_filename="other.txt",
		file_type="txt",
		file_size_bytes=10,
		status=DocumentStatus.INDEXED,
		pinecone_namespace="other",
		chunk_count=1,
	)
	test_db.add(other_doc)
	await test_db.commit()
	await test_db.refresh(other_doc)

	response = await async_client.delete(f"/api/v1/documents/{other_doc.id}", headers=auth_headers)
	assert response.status_code == 404
