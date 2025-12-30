import uuid
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_task_crud_and_pagination():
    """
    End-to-end ASYNC API test (production-grade).

    Covers:
    - User registration
    - JWT login
    - Task creation
    - Cursor/limit pagination

    DESIGN NOTES (IMPORTANT):

    1) Fully async:
       - Matches FastAPI async lifecycle
       - Matches async SQLAlchemy engine
       - Single event loop (no deadlocks)

    2) Celery is mocked (via conftest):
       - No Redis dependency
       - No background retries
       - Deterministic CI behavior

    3) Pagination contract is enforced:
       - items[] list
       - meta object with limit + has_more
    """

    async with AsyncClient(
        app=app,
        base_url="http://localhost",  # TrustedHostMiddleware-safe
    ) as client:

        username = f"user_{uuid.uuid4().hex[:8]}"
        password = "StrongPass123"

        # ----------------------------
        # Register
        # ----------------------------
        res = await client.post(
            "/auth/register",
            json={"username": username, "password": password},
        )
        assert res.status_code == 201

        # ----------------------------
        # Login
        # ----------------------------
        res = await client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        assert res.status_code == 200

        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ----------------------------
        # Create tasks
        # ----------------------------
        for i in range(5):
            res = await client.post(
                "/tasks/",  # trailing slash REQUIRED
                json={"title": f"Task {i}"},
                headers=headers,
            )
            assert res.status_code == 201

        # ----------------------------
        # Paginated fetch
        # ----------------------------
        res = await client.get(
            "/tasks/?limit=2&offset=0",
            headers=headers,
        )
        assert res.status_code == 200

        payload = res.json()

        # ----------------------------
        # Pagination contract assertions
        # ----------------------------
        assert "items" in payload
        assert "meta" in payload

        items = payload["items"]
        meta = payload["meta"]

        assert isinstance(items, list)
        assert len(items) == 2

        assert meta["limit"] == 2
        assert meta["has_more"] is True
