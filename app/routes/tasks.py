# app/routes/tasks.py
"""
Task routes:
- Create tasks
- List tasks (paginated)
- Delete tasks

All routes are JWT-protected.
"""

import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.pagination_schema import Page, PageMeta
from app.schemas.task_schema import TaskCreate, TaskResponse


router = APIRouter(prefix="/tasks", tags=["Tasks"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ------------------------------------------------------------
# Auth dependency
# ------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user


# ------------------------------------------------------------
# Create task
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_task = Task(
        id=str(uuid.uuid4()),
        title=task.title,
        description=task.description,
        owner_id=user.id,
        created_at=datetime.utcnow(),
    )

    db.add(new_task)
    await db.commit()

    return TaskResponse(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        owner=user.username,
        created_at=new_task.created_at,
    )


# ------------------------------------------------------------
# List tasks (paginated)
# ------------------------------------------------------------
@router.get("/", response_model=Page[TaskResponse])
async def get_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    stmt = (
        select(Task)
        .where(Task.owner_id == user.id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit + 1)  # fetch one extra to detect has_more
    )

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    has_more = len(tasks) > limit
    tasks = tasks[:limit]

    items = [
        TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            owner=user.username,
            created_at=t.created_at,
        )
        for t in tasks
    ]

    return Page(
        items=items,
        meta=PageMeta(
            limit=limit,
            has_more=has_more,
            next_cursor=None,
        ),
    )


# ------------------------------------------------------------
# Delete task
# ------------------------------------------------------------
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = delete(Task).where(
        Task.id == task_id,
        Task.owner_id == user.id,
    )

    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or unauthorized",
        )

    return None
