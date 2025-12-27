# app/tests/test_idempotency.py

import uuid
import pytest

from app.idempotency import (
    mark_job_started,
    get_job_result,
    save_job_result,
)


@pytest.mark.asyncio
async def test_idempotent_job_execution(db_session):
    """
    Ensure idempotent background job behavior using SQL job_log table.
    """

    job_id = f"job:{uuid.uuid4()}"

    # First execution
    await mark_job_started(db_session, job_id)

    # Duplicate execution (should be ignored)
    await mark_job_started(db_session, job_id)

    # No result yet
    assert await get_job_result(db_session, job_id) is None

    # Save job result
    result = {"email": "sent"}
    await save_job_result(db_session, job_id, result)

    # Result must be retrievable and stable
    stored = await get_job_result(db_session, job_id)
    assert stored == result
