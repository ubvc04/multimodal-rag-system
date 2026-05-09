"""Alembic environment configuration."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.config import settings  # noqa: E402
from app.models import Base  # noqa: E402

config = context.config
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
	fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
	"""Run migrations in offline mode."""
	url = config.get_main_option("sqlalchemy.url")
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
	context.configure(connection=connection, target_metadata=target_metadata)

	with context.begin_transaction():
		context.run_migrations()


async def run_migrations_online() -> None:
	"""Run migrations in online mode using async engine."""
	connectable: AsyncEngine = create_async_engine(
		settings.DATABASE_URL,
		poolclass=pool.NullPool,
	)

	async with connectable.connect() as connection:
		await connection.run_sync(do_run_migrations)

	await connectable.dispose()


if context.is_offline_mode():
	run_migrations_offline()
else:
	asyncio.run(run_migrations_online())
