# app/database.py

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# Globals to store client and db instance
client: AsyncIOMotorClient | None = None
db = None


async def connect_to_mongo(force: bool = False):
    """
    Connect to MongoDB or reconnect if the client was closed.
    This prevents CI tests from failing due to a dead MongoClient.
    """
    global client, db

    # If a client already exists and we are not forcing a reconnect,
    # check if the client is still alive.
    if client is not None and not force:
        try:
            await client.admin.command("ping")  # Check if alive
            return  # Client is alive, no need to reconnect
        except Exception:
            pass  # Client is dead → reconnect

    # Create a brand new client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    print("✅ MongoDB connected successfully.")


async def close_mongo_connection():
    """Close MongoDB connection on FastAPI shutdown."""
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed.")
