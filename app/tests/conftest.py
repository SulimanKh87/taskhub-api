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
        tx = await session.begin()
        try:
            yield session
        finally:
            # Always rollback, even if the test fails mid-way
            if tx.is_active:
                await tx.rollback()