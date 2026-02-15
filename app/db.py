# app/db.py
"""
Database wiring: engine + sessionmaker + FastAPI dependency.

Key points:
- `SessionLocal` is a *session factory* (async_sessionmaker), not a global session.
- In tests we use NullPool to avoid:
  - event-loop reuse issues
  - cross-test connection reuse
- get_db() yields one session per request and always closes it.
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.base import Base


def _create_engine() -> AsyncEngine:
    is_test = settings.env.lower() == "test"

    poolclass = NullPool if is_test else None

    return create_async_engine(
        settings.database_url,
        echo=settings.sql_echo,
        future=True,
        poolclass=poolclass,
        pool_pre_ping=not is_test,
    )


engine: AsyncEngine = _create_engine()

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


# ------------------------------------------------------------
# Import ORM models so Alembic can discover them
# ------------------------------------------------------------
from app.models.user import User
from app.models.task import Task
from app.models.job_log import JobLog
