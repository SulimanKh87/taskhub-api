import pytest
from app.database import connect_to_mongo, close_mongo_connection
from app import database


@pytest.mark.asyncio
async def test_required_indexes_exist():
    """
    Ensure MongoDB indexes are created on startup.
    """

    await connect_to_mongo()

    task_indexes = await database.db.tasks.index_information()
    user_indexes = await database.db.users.index_information()
    job_indexes = await database.db.job_log.index_information()

    assert "idx_tasks_owner_created_at" in task_indexes
    assert "idx_users_username" in user_indexes
    assert "idx_job_log_job_id" in job_indexes

    await close_mongo_connection()
