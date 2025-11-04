from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserModel(BaseModel):
    """MongoDB document model for users."""
    id: Optional[str] = Field(alias="_id", default=None)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Enable aliasing for MongoDB’s "_id"
        populate_by_name = True
        from_attributes = True
