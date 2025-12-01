import uuid

import pytest
from httpx import AsyncClient

from app.database import connect_to_mongo, close_mongo_connection  # DB handling
from app import database
from app.main import app  # FastAPI instance
from app.workers.celery_app import celery_app  # Celery worker instance


@pytest.mark.asyncio
async def test_idempotent_welcome_email():
    """Ensure Celery background job runs idempotently (no duplicates)."""

    # --- Ensure DB is ready ---
    await connect_to_mongo()
    await database.db.job_log.delete_many({})  # clean for test isolation

    # === 1. Register a new user ===
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPass123!"

    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.post(
            "/auth/register",
            json={"username": username, "password": password},
        )

    assert res.status_code == 201
    user_id = res.json()["id"]

    # job_id uses same format defined in auth.py
    job_id = f"welcome_email:{user_id}"

    # === 2. Trigger Celery job twice (simulate duplicate retries) ===
    result1 = celery_app.send_task(
        "taskhub.send_welcome_email", args=[username, job_id]
    ).get(timeout=10)

    result2 = celery_app.send_task(
        "taskhub.send_welcome_email", args=[username, job_id]
    ).get(timeout=10)

    # === 3. Both results MUST be identical ===
    assert result1 == result2

    # === 4. Mongo should contain exactly ONE job_log entry ===
    job_records = await database.db.job_log.find({"job_id": job_id}).to_list(length=10)

    assert len(job_records) == 1
    assert job_records[0]["status"] == "completed"
    assert "result" in job_records[0]

    # --- Clean shutdown ---
    await close_mongo_connection()
