from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TaskModel(BaseModel):
    """MongoDB document model for tasks."""
    id: Optional[str] = Field(alias="_id", default=None)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="")
    status: str = Field(default="pending")
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True
