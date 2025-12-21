import pytest
from httpx import AsyncClient

from app.database import connect_to_mongo, close_mongo_connection
from app.main import app
from app import database


@pytest.mark.asyncio
async def test_task_crud_and_pagination():
    """
    End-to-end test covering:
    - User registration & login
    - Task creation
    - Offset-based pagination
    - Correct Page[T] response shape
    """

    # --------------------------------------------------
    # Database setup (clean state)
    # --------------------------------------------------
    await connect_to_mongo()
    await database.db.users.delete_many({})
    await database.db.tasks.delete_many({})

    async with AsyncClient(app=app, base_url="http://test") as client:

        # -------------------------
        # Register user
        # -------------------------
        res = await client.post(
            "/auth/register",
            json={"username": "alice", "password": "StrongPass123"},
        )
        assert res.status_code == 201

        # -------------------------
        # Login
        # -------------------------
        res = await client.post(
            "/auth/login",
            data={"username": "alice", "password": "StrongPass123"},
        )
        assert res.status_code == 200

        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # -------------------------
        # Create tasks
        # -------------------------
        for i in range(5):
            res = await client.post(
                "/tasks/",
                json={"title": f"Task {i}", "description": "test"},
                headers=headers,
            )
            assert res.status_code == 201

        # -------------------------
        # Page 1
        # -------------------------
        res = await client.get("/tasks/?limit=2&skip=0", headers=headers)
        assert res.status_code == 200

        page1 = res.json()
        assert "items" in page1
        assert "meta" in page1

        assert len(page1["items"]) == 2
        assert page1["meta"]["has_more"] is True
        assert page1["meta"]["limit"] == 2

        # -------------------------
        # Page 2
        # -------------------------
        res = await client.get("/tasks/?limit=2&skip=2", headers=headers)
        page2 = res.json()

        assert len(page2["items"]) == 2
        assert page2["meta"]["has_more"] is True

        # -------------------------
        # Page 3 (last page)
        # -------------------------
        res = await client.get("/tasks/?limit=2&skip=4", headers=headers)
        page3 = res.json()

        assert len(page3["items"]) == 1
        assert page3["meta"]["has_more"] is False

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------
    await close_mongo_connection()
