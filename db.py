# app/db.py

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ------------------------------------------------------------
# SQLAlchemy Base
# ------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ------------------------------------------------------------
# Async Engine & Session
# ------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=False,              # set True only for debugging
    future=True,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ------------------------------------------------------------
# FastAPI dependency
# ------------------------------------------------------------
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
