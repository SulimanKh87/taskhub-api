from pydantic import BaseModel, Field
from datetime import datetime

# ==========================
# USER SCHEMAS
# ==========================

class UserBase(BaseModel):
    """Shared user fields."""
    # Defines common attributes for all user schemas.
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    # '...' means required, and validations ensure 3–50 characters.


class UserCreate(UserBase):
    """Schema for user registration requests."""
    # Used when users register. Includes password for hashing.
    password: str = Field(..., min_length=6, description="Secure password")


class UserLogin(UserBase):
    """Schema for login requests."""
    # Used for login — same structure but typically handled via OAuth2 form.
    password: str


class UserInDB(UserBase):
    """Internal schema stored in DB (not exposed externally)."""
    # This represents what is saved in MongoDB.
    id: str                      # Unique user identifier
    hashed_password: str         # Hashed password (never returned to client)
    created_at: datetime         # When the user was created

    class Config:
        orm_mode = True          # Enables model → dict serialization for database data


class UserPublic(UserBase):
    """Schema returned to API clients (no password exposure)."""
    # Used in API responses (like /register).
    id: str                      # User ID returned to client
    created_at: datetime         # Creation timestamp

    class Config:
        orm_mode = True          # Same reason: allows conversion from ORM/Mongo objects
