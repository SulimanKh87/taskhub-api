import pytest  # Pytest is used for automated testing
from httpx import AsyncClient  # HTTPX allows async HTTP requests to FastAPI

from app.database import connect_to_mongo, close_mongo_connection  # DB connection handlers
from app.main import app  # Import the FastAPI application instance


# This test checks whether the /health endpoint is working properly
@pytest.mark.asyncio
async def test_health_check():
    """Ensure health endpoint works and DB is initialized."""
    await connect_to_mongo()  # Make sure DB is ready before testing

    async with AsyncClient(app=app, base_url="http://test") as client: # Create async HTTP client
        res = await client.get("/health") # Call the health endpoint

    assert res.status_code == 200 # Verify we got a successful response
    assert res.json()["status"] == "ok" # Check response content

    await close_mongo_connection()  # Clean shutdown