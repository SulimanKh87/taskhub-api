from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from pymongo import ReturnDocument
from app.config import settings
from app.database import db
from app.schemas import UserCreate, UserLogin, UserPublic, Token
import uuid
import asyncio

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================
# Helper Functions
# ==========================

def hash_password(password: str) -> str:
    """Securely hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain password with hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: int = settings.jwt_expire_minutes):
    """Generate JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


# ==========================
# Register New User
# ==========================

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(user.password)
    new_user = {
        "_id": str(uuid.uuid4()),
        "username": user.username,
        "hashed_password": hashed_pw,
        "created_at": datetime.utcnow(),
    }

    await db.users.insert_one(new_user)
    return UserPublic(id=new_user["_id"], username=user.username, created_at=new_user["created_at"])


# ==========================
# Login and Get Token
# ==========================

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_access_token(data={"sub": user["username"]}, expires_delta=settings.jwt_refresh_days * 1440)

    return Token(access_token=access_token, refresh_token=refresh_token)
