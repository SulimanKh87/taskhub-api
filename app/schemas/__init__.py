# This file makes the `schemas` directory a Python package
# It also provides convenient imports, so you can do:
#     from app.schemas import UserCreate, TaskResponse, Token
# instead of importing from each individual file.

from .user_schema import (        # Import all user-related schemas
    UserBase,                     # Common user fields
    UserCreate,                   # Used for registration requests
    UserLogin,                    # Used for login requests
    UserInDB,                     # Internal DB model (with password hash)
    UserPublic,                   # Public-facing user info
)
from .task_schema import (        # Import task-related schemas
    TaskBase,                     # Shared task fields
    TaskCreate,                   # Schema for creating new tasks
    TaskInDB,                     # Internal DB model (Mongo)
    TaskResponse,                 # Schema for responses sent to clients
)
from .token_schema import (       # Import token-related schemas
    Token,                        # Represents the JWT response returned to users
    TokenPayload,                 # Represents the contents of a decoded JWT
)
