# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.mongodb_db]
