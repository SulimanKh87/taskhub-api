# Handles user authentication (register + login) using JWT and bcrypt

import uuid  # Used to generate unique user IDs
from datetime import datetime, timedelta  # Used to manage token expiration times
from app.workers.celery_app import celery_app

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)  # FastAPI utilities for routing, dependency injection, and HTTP errors
from fastapi.security import (
    OAuth2PasswordRequestForm,
)  # Handles form-based login requests (username/password)
from jose import jwt  # Library to encode/decode JWT tokens
from passlib.context import (
    CryptContext,
)  # Provides password hashing and verification with bcrypt

from app.config import settings  # Import global configuration (.env-loaded)
from app import database  # MongoDB async client (Motor)
from app.schemas.token_schema import Token

# Pydantic schemas for validation
from app.schemas.user_schema import UserCreate, UserPublic

# Create a router instance for all /auth routes
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Create a password hashing context — bcrypt is the algorithm
import os
from passlib.context import CryptContext

if os.getenv("ENV") == "test":
    # Use fast, stable hashing during tests
    pwd_context = CryptContext(
        schemes=["sha256_crypt"],
        deprecated="auto",
    )
else:
    # Production password hashing
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
    )


# ==========================
# Helper Functions
# ==========================


def hash_password(password: str) -> str:
    """Securely hash a password."""
    # Takes a plain password and returns a bcrypt hash
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain password with hash."""
    # Verifies that the plain text password matches the stored hash
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: int = settings.jwt_expire_minutes):
    """Generate JWT token."""
    # Creates a JSON Web Token (JWT) with an expiration time
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta
    )  # Expiration timestamp
    to_encode.update({"exp": expire})  # Add expiry claim to payload
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


# ==========================
# Register New User
# ==========================


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserCreate):
    # Check if the username already exists in MongoDB
    existing = await database.db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password before saving it
    hashed_pw = hash_password(user.password)

    # Create the user document
    new_user = {
        "_id": str(uuid.uuid4()),  # Generate unique ID
        "username": user.username,
        "hashed_password": hashed_pw,
        "created_at": datetime.utcnow(),  # Record creation timestamp
    }

    # Insert user into MongoDB
    await database.db.users.insert_one(new_user)

    # ==========================
    # IDEMPOTENT BACKGROUND JOB
    # ==========================

    # Unique idempotency key for this logical email
    job_id = f"welcome_email:{new_user['_id']}"

    # Pass email + job_id to Celery
    celery_app.send_task(
        "taskhub.send_welcome_email",
        args=[new_user["username"], job_id],
    )

    # Return public user info (excluding password)
    return UserPublic(
        id=new_user["_id"], username=user.username, created_at=new_user["created_at"]
    )


# ==========================
# Login and Get Token
# ==========================


@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm extracts username/password from form-data body
    user = await database.db.users.find_one({"username": form_data.username})

    # Check if user exists and password is valid
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate access token (short-lived)
    access_token = create_access_token(data={"sub": user["username"]})

    # Generate refresh token (longer expiration)
    refresh_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=settings.jwt_refresh_days * 1440,  # convert days → minutes
    )

    # Return both tokens to the client
    return Token(access_token=access_token, refresh_token=refresh_token)
