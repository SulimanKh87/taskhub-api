"""
Pytest fixtures for TaskHub API.

Key design goals:
- Fully async (FastAPI + SQLAlchemy)
- Real PostgreSQL DB
- NO Redis / NO Celery broker during tests
- Deterministic, CI-safe execution
"""

import os
import pytest
import pytest_asyncio
from sqlalchemy import text

# ------------------------------------------------------
# Environment setup (must run BEFORE app import)
# ------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://taskhub:taskhub_pass@localhost:5432/taskhub",
)

# ------------------------------------------------------
# Imports AFTER env is set
# ------------------------------------------------------
from app.db import engine, SessionLocal  # noqa: E402
from app.models.base import Base  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_schema():
    """Create DB schema once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """
    Clean DB before each test.

    Why:
    - Prevent state leakage
    - Deterministic tests
    """
    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE TABLE job_log, tasks, users RESTART IDENTITY CASCADE;")
        )
    yield


@pytest.fixture(autouse=True)
def disable_celery_tasks(monkeypatch):
    """
    CRITICAL TEST ISOLATION FIX.

    Why this exists:
    ----------------
    - API routes trigger Celery tasks
    - Celery uses Redis (not available in pytest)
    - Redis retries cause tests to hang for ~60s

    What we do:
    -----------
    We monkeypatch `celery_app.send_task` so:
    - No Redis connection is attempted
    - API behavior remains identical
    - Background jobs are tested separately

    This is standard practice in production backends.
    """

    def _noop_send_task(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.routes.auth.celery_app.send_task",
        _noop_send_task,
    )


@pytest_asyncio.fixture
async def db_session():
    """Direct DB access for unit tests."""
    async with SessionLocal() as session:
        yield session
