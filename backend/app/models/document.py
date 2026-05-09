"""Document model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


class DocumentStatus(str, Enum):
	"""Processing status of a document."""

	PENDING = "pending"
	PROCESSING = "processing"
	INDEXED = "indexed"
	FAILED = "failed"


class Document(Base):
	"""Stored user document."""

	__tablename__ = "documents"

	id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
	filename: Mapped[str] = mapped_column(String(512), nullable=False)
	original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
	file_type: Mapped[str] = mapped_column(String(50), nullable=False)
	file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(SqlEnum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING)
	pinecone_namespace: Mapped[str] = mapped_column(String(255), nullable=False)
	chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
	metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
	)

	user = relationship("User", back_populates="documents")
