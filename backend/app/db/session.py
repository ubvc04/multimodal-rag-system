"""Async SQLAlchemy session setup."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


async_engine: AsyncEngine = create_async_engine(
	settings.DATABASE_URL,
	pool_size=settings.DATABASE_POOL_SIZE,
	max_overflow=settings.DATABASE_MAX_OVERFLOW,
	pool_pre_ping=True,
	pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	"""Provide a transactional scope around a series of operations."""
	session: AsyncSession = AsyncSessionLocal()
	try:
		yield session
		await session.commit()
	except Exception:
		await session.rollback()
		raise
	finally:
		await session.close()
