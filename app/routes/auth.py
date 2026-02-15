# app/routes/auth.py
# Handles user authentication (register + login) using JWT and SQLAlchemy

import uuid
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.token_schema import Token
from app.schemas.user_schema import UserCreate, UserPublic
from app.utils.security import hash_password, verify_password
from app.workers.celery_app import celery_app


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ------------------------------------------------------------
# Helper: create JWT token
# ------------------------------------------------------------
def create_access_token(
    data: dict,
    expires_delta: int = settings.jwt_expire_minutes,
):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


# ------------------------------------------------------------
# Register
# ------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    new_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        hashed_password=hash_password(user.password),
        created_at=datetime.utcnow(),
    )

    db.add(new_user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    # --------------------------------------------------------
    # Idempotent welcome email
    # --------------------------------------------------------
    job_id = f"welcome_email:{new_user.id}"

    celery_app.send_task(
        "tasks.send_welcome_email",
        args=[new_user.username, job_id],
    )

    return UserPublic(
        id=new_user.id,
        username=new_user.username,
        created_at=new_user.created_at,
    )


# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    access_token = create_access_token({"sub": user.username})
    refresh_token = create_access_token(
        {"sub": user.username},
        expires_delta=settings.jwt_refresh_days * 1440,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )
