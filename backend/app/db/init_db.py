"""Database initialization helpers."""

from __future__ import annotations

from app.db.session import async_engine
from app.models import Base


async def create_tables() -> None:
	"""Create all database tables."""
	async with async_engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
	"""Drop all database tables (testing only)."""
	async with async_engine.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)
