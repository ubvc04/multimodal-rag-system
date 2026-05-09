"""User model."""

from __future__ import annotations

from uuid import uuid4

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


class User(Base):
	"""Application user."""

	__tablename__ = "users"

	id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
	hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
	full_name: Mapped[str] = mapped_column(String(255), nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
	)

	documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
