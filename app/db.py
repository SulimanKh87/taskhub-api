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


def _normalize_async_db_url(url: str) -> str:
    # SQLAlchemy async engine requires an async driver (asyncpg)
    # Accept "postgresql://" but convert it to "postgresql+asyncpg://"
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _create_engine() -> AsyncEngine:
    is_test = settings.env.lower() == "test"

    poolclass = NullPool if is_test else None

    url = _normalize_async_db_url(settings.database_url)

    engine_kwargs: dict = {
        "echo": settings.sql_echo,
        "future": True,
        "pool_pre_ping": not is_test,
    }

    if is_test:
        engine_kwargs["poolclass"] = NullPool
    else:
        # AWS/RDS-friendly defaults (safe for Fargate)
        engine_kwargs.update(
            pool_size=getattr(settings, "db_pool_size", 5),
            max_overflow=getattr(settings, "db_max_overflow", 10),
            pool_timeout=getattr(settings, "db_pool_timeout", 30),
            pool_recycle=getattr(settings, "db_pool_recycle_seconds", 1800),
        )

    return create_async_engine(url, **engine_kwargs)


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
