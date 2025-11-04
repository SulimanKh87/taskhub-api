from pydantic import BaseModel, Field
from datetime import datetime


# ==========================
# USER SCHEMAS
# ==========================

class UserBase(BaseModel):
    """Shared user fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")


class UserCreate(UserBase):
    """Schema for user registration requests."""
    password: str = Field(..., min_length=6, description="Secure password")


class UserLogin(UserBase):
    """Schema for login requests."""
    password: str


class UserInDB(UserBase):
    """Internal schema stored in DB (not exposed externally)."""
    id: str
    hashed_password: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserPublic(UserBase):
    """Schema returned to API clients (no password exposure)."""
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
