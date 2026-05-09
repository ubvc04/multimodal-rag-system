"""Query log model."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import Base


class QueryLog(Base):
	"""Track user queries and responses."""

	__tablename__ = "query_logs"

	id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
	document_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
	query_text: Mapped[str] = mapped_column(Text, nullable=False)
	response_text: Mapped[str] = mapped_column(Text, nullable=False)
	sources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
	latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
	token_count_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
	token_count_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
	model_used: Mapped[str] = mapped_column(String(255), nullable=False)
	agent_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
