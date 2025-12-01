# app/database.py
import motor
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# Globals to store client and db instance
client = None
db = None


async def connect_to_mongo():
    """Initialize MongoDB connection on FastAPI startup."""

    async def connect_to_mongo(force: bool = False):
        global client, db

        # If the client exists but was closed, reconnect
        if client is not None and not force:
            try:
                # Try a simple command to check if client is alive
                await client.admin.command("ping")
                return  # client is alive — no reconnect needed
            except Exception:
                pass  # dead client → reconnect

        # Always reconnect if force=True OR client was dead
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db]
        print("✅ MongoDB connected successfully.")


async def close_mongo_connection():
    """Close MongoDB connection on FastAPI shutdown."""
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed.")
