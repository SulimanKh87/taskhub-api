from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================
# TASK SCHEMAS
# ==========================

class TaskBase(BaseModel):
    """Shared fields for tasks."""
    # This base class defines common fields shared between create, DB, and response models.
    title: str = Field(..., min_length=3, max_length=100, description="Title of the task")
    # The '...' means this field is required. It also has validation constraints.
    description: Optional[str] = Field(default="", max_length=500)
    # Optional description field, defaults to empty string.
    owner: Optional[str] = Field(default=None, description="Username of the task owner")
    # Owner name is optional here, filled after user authentication.


class TaskCreate(TaskBase):
    """Schema for creating new tasks."""
    # Inherits from TaskBase; no extra fields are required for task creation.
    pass


class TaskInDB(TaskBase):
    """Internal DB model for Mongo documents."""
    id: str                      # Represents MongoDB document _id as string
    created_at: datetime         # Timestamp when the task was created

    class Config:
        orm_mode = True          # Allows compatibility with ORM or MongoDB-like objects


class TaskResponse(TaskBase):
    """Response model returned to API clients."""
    id: str                      # Unique task identifier returned to clients
    created_at: datetime         # When the task was created

    class Config:
        orm_mode = True          # Enables model-to-dict conversion when returning responses
