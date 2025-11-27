# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# Globals to store client and db instance
client = None
db = None


async def connect_to_mongo():
    """Initialize MongoDB connection on FastAPI startup."""
    global client, db
    if client is None:  # Prevent reconnecting multiple times
        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db]
        print("✅ MongoDB connected successfully.")


async def close_mongo_connection():
    """Close MongoDB connection on FastAPI shutdown."""
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed.")
