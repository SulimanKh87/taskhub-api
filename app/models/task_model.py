# Defines how a task document looks in MongoDB

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TaskModel(BaseModel):
    """MongoDB document model for tasks."""
    id: Optional[str] = Field(alias="_id", default=None)             # Mongo _id alias
    title: str = Field(..., min_length=1, max_length=200)            # Required task title
    description: Optional[str] = Field(default="")                   # Optional description
    status: str = Field(default="pending")                           # Default task status
    owner_id: str                                                    # User ID of owner
    created_at: datetime = Field(default_factory=datetime.utcnow)    # Created timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)    # Updated timestamp

    class Config:
        populate_by_name = True
        from_attributes = True
