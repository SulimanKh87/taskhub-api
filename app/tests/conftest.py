# app/tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session


@pytest.fixture
async def db_session() -> AsyncSession:
    """
    Provides an isolated SQLAlchemy session per test.

    Each test runs inside a transaction that is rolled back,
    guaranteeing a clean database state.
    """
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()
