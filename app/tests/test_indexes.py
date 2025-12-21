import pytest

# Import explicit DB lifecycle helpers
# These ensure MongoDB is initialized exactly as in production
from app.database import connect_to_mongo, close_mongo_connection
from app import database


@pytest.mark.asyncio
async def test_required_indexes_exist():
    """
    Verify that required MongoDB indexes are created automatically
    during application startup.

    This test ensures:
    - Index initialization logic runs successfully
    - Index names are stable and predictable
    - Startup behavior in CI matches production behavior
    """

    # --------------------------------------------------
    # Arrange: initialize MongoDB connection
    #
    # connect_to_mongo() triggers ensure_indexes()
    # which creates all required indexes idempotently.
    # --------------------------------------------------
    await connect_to_mongo()

    # --------------------------------------------------
    # Act: retrieve index metadata from MongoDB
    #
    # index_information() returns a dict where keys
    # are index names and values contain index specs.
    # --------------------------------------------------
    task_indexes = await database.db.tasks.index_information()
    user_indexes = await database.db.users.index_information()
    job_indexes = await database.db.job_log.index_information()

    # --------------------------------------------------
    # Assert: verify required indexes exist
    #
    # These names must match those defined in database.py.
    # If any index is missing, this test will fail,
    # preventing performance regressions.
    # --------------------------------------------------
    assert "idx_tasks_owner_created_at" in task_indexes
    assert "idx_users_username" in user_indexes
    assert "idx_job_log_job_id" in job_indexes

    # --------------------------------------------------
    # Cleanup: close MongoDB connection
    #
    # Ensures clean shutdown and avoids connection leaks
    # during test execution.
    # --------------------------------------------------
    await close_mongo_connection()
