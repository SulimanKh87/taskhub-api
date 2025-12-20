"""
MongoDB connection management and index initialization.

This module:
- Manages the Motor client lifecycle
- Ensures required indexes exist on startup
"""

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# Global Mongo client and DB reference
client: AsyncIOMotorClient | None = None
db = None


async def ensure_indexes():
    """
    Ensure MongoDB indexes required for scalable queries.

    Indexes are created idempotently and are safe to run on every startup.
    """
    # Supports task pagination by owner and creation time
    await db.tasks.create_index([("owner", 1), ("created_at", -1)])


async def connect_to_mongo(force: bool = False):
    """
    Establish MongoDB connection.

    Reuses existing client if alive unless forced to reconnect.
    """
    global client, db

    if client is not None and not force:
        try:
            await client.admin.command("ping")
            return
        except Exception:
            pass

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    # Ensure DB indexes on startup
    await ensure_indexes()

    print("✅ MongoDB connected successfully.")


async def close_mongo_connection():
    """
    Close MongoDB connection on application shutdown.
    """
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed.")
