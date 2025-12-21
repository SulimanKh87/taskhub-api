"""
MongoDB connection management and index initialization.

This module is responsible for:
- Creating and managing the MongoDB client (Motor)
- Initializing required MongoDB indexes on application startup
- Closing the connection on shutdown

Indexes are created in code (not manually) to ensure:
- Consistency across environments
- CI/CD safety
- Scalability from day one
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# -------------------------------------------------------------------
# Global Mongo client and database reference
# -------------------------------------------------------------------
client: AsyncIOMotorClient | None = None
db = None


# -------------------------------------------------------------------
# Index initialization
# -------------------------------------------------------------------
async def ensure_indexes():
    """
    Ensure MongoDB indexes required for scalable queries.

    IMPORTANT:
    - create_index is idempotent (safe to run multiple times)
    - This function is called on every application startup
    - MongoDB will only create the index once if it already exists
    """

    # ---------------------------------------------------------------
    # TASKS COLLECTION
    #
    # Used by:
    # db.tasks.find({ owner }).sort(created_at desc)
    #
    # Supports:
    # - Fast filtering by owner
    # - Efficient pagination ordered by creation time
    # ---------------------------------------------------------------
    await db.tasks.create_index(
        [("owner", 1), ("created_at", -1)],
        name="idx_tasks_owner_created_at",
    )

    # ---------------------------------------------------------------
    # USERS COLLECTION
    #
    # Used by:
    # - Registration (unique username check)
    # - Login (username lookup)
    #
    # Enforces uniqueness at the DB level (race-condition safe)
    # ---------------------------------------------------------------
    await db.users.create_index(
        "username",
        unique=True,
        name="idx_users_username",
    )

    # ---------------------------------------------------------------
    # JOB_LOG COLLECTION
    #
    # Used for idempotent Celery background jobs
    #
    # Guarantees:
    # - Only one logical job execution per job_id
    # - Safe retries without duplication
    # ---------------------------------------------------------------
    await db.job_log.create_index(
        "job_id",
        unique=True,
        name="idx_job_log_job_id",
    )


# -------------------------------------------------------------------
# MongoDB connection lifecycle
# -------------------------------------------------------------------
async def connect_to_mongo(force: bool = False):
    """
    Establish a MongoDB connection.

    - Reuses existing client if alive
    - Reconnects automatically if the client is dead
    - Ensures required indexes exist after connecting
    """
    global client, db

    # If a client already exists, verify it's still alive
    if client is not None and not force:
        try:
            await client.admin.command("ping")
            return
        except Exception:
            # Client is dead → reconnect
            pass

    # Create a new MongoDB client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    # 🔥 CRITICAL STEP:
    # Create / verify all required indexes on startup
    await ensure_indexes()

    print("✅ MongoDB connected & indexes ensured.")


async def close_mongo_connection():
    """
    Close MongoDB connection on application shutdown.
    """
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed.")
