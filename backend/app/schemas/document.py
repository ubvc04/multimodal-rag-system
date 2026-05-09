"""Document schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


class DocumentResponse(BaseModel):
	"""Document response payload."""

	id: UUID
	filename: str
	original_filename: str
	file_type: str
	file_size_bytes: int
	status: str
	pinecone_namespace: str
	chunk_count: int
	error_message: str | None
	created_at: datetime
	updated_at: datetime

	model_config = SettingsConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
	"""Paginated list of documents."""

	items: list[DocumentResponse]
	total: int = Field(..., ge=0)
	skip: int = Field(..., ge=0)
	limit: int = Field(..., ge=1)
