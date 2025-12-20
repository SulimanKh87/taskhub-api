import pytest
from httpx import AsyncClient

from app.database import connect_to_mongo, close_mongo_connection
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """
    Ensure the health endpoint works and the app boots correctly.
    """
    await connect_to_mongo()

    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.get("/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    await close_mongo_connection()
