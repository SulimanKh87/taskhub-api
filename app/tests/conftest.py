# app/tests/conftest.py
"""
Pytest fixtures for TaskHub API.
"""

import os
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

os.environ.setdefault("ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://taskhub:taskhub@localhost:5432/taskhub",
)

from app.models.base import Base  # noqa: E402


def get_test_engine():
    """Create a fresh engine for each use — avoids cross-loop issues."""
    url = os.environ["DATABASE_URL"]
    return create_async_engine(url, poolclass=NullPool)


@pytest_asyncio.fixture(autouse=True)
async def create_schema():
    """Create DB schema before each test."""
    engine = get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Truncate all tables before each test — uses IF EXISTS to handle first run."""
    engine = get_test_engine()
    async with engine.begin() as conn:
        # IF EXISTS prevents failure when tables don't exist yet on first run
        await conn.execute(text("TRUNCATE TABLE IF EXISTS job_log, tasks, users RESTART IDENTITY CASCADE;"))
    await engine.dispose()
    yield


@pytest.fixture(autouse=True)
def disable_celery_tasks(monkeypatch):
    def _noop_send_task(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.routes.auth.celery_app.send_task",
        _noop_send_task,
    )


@pytest_asyncio.fixture
async def db_session():
    """Direct DB access for unit tests."""
    engine = get_test_engine()
    Session = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
