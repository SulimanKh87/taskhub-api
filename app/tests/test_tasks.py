import pytest
from httpx import AsyncClient

from app.database import connect_to_mongo, close_mongo_connection
from app.main import app
from app import database


@pytest.mark.asyncio
async def test_task_crud_and_pagination():
    """
    Full end-to-end test:
    - Register user
    - Login
    - Create multiple tasks
    - Verify paginated task listing
    """
    await connect_to_mongo()
    await database.db.users.delete_many({})
    await database.db.tasks.delete_many({})

    async with AsyncClient(app=app, base_url="http://test") as client:
        # --- Register ---
        res = await client.post(
            "/auth/register",
            json={"username": "alice", "password": "StrongPass123"},
        )
        assert res.status_code == 201

        # --- Login ---
        res = await client.post(
            "/auth/login",
            data={"username": "alice", "password": "StrongPass123"},
        )
        assert res.status_code == 200
        token = res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # --- Create tasks ---
        for i in range(5):
            res = await client.post(
                "/tasks/",
                json={"title": f"Task {i}", "description": "test"},
                headers=headers,
            )
            assert res.status_code == 201

        # --- Page 1 ---
        res = await client.get("/tasks/?limit=2&skip=0", headers=headers)
        assert res.status_code == 200
        page1 = res.json()
        assert len(page1) == 2

        # --- Page 2 ---
        res = await client.get("/tasks/?limit=2&skip=2", headers=headers)
        assert res.status_code == 200
        page2 = res.json()
        assert len(page2) == 2

        # --- Page 3 ---
        res = await client.get("/tasks/?limit=2&skip=4", headers=headers)
        assert res.status_code == 200
        page3 = res.json()
        assert len(page3) == 1

    await close_mongo_connection()
