# Defines how a user document looks inside MongoDB (schema-level validation via Pydantic)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    """MongoDB document model for users."""

    id: Optional[str] = Field(alias="_id", default=None)  # MongoDB _id field alias
    username: str = Field(
        ..., min_length=3, max_length=50
    )  # Username must be 3–50 chars
    email: EmailStr  # Validated email address
    hashed_password: str  # Stored securely (bcrypt)
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )  # Timestamp of creation

    class Config:
        # Enable aliasing for MongoDB’s "_id"
        populate_by_name = True
        from_attributes = True  # Allow ORM or DB-like objects to map directly
