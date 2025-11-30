# Defines how a user document looks inside MongoDB (schema-level validation via Pydantic)
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    """MongoDB document model for users."""

    id: Optional[str] = Field(alias="_id", default=None)
    username: str = Field(..., min_length=3, max_length=50)

    # Email no longer required — optional for simple TaskHub project
    email: Optional[EmailStr] = None

    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True
