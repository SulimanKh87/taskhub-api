from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==========================
# TASK SCHEMAS
# ==========================

class TaskBase(BaseModel):
    """Shared fields for tasks."""
    title: str = Field(..., min_length=3, max_length=100, description="Title of the task")
    description: Optional[str] = Field(default="", max_length=500)
    owner: Optional[str] = Field(default=None, description="Username of the task owner")


class TaskCreate(TaskBase):
    """Schema for creating new tasks."""
    pass


class TaskInDB(TaskBase):
    """Internal DB model for Mongo documents."""
    id: str
    created_at: datetime

    class Config:
        orm_mode = True


class TaskResponse(TaskBase):
    """Response model returned to API clients."""
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
