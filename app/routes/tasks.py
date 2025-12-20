"""
Task routes:
- Create tasks
- List tasks (paginated)
- Delete tasks

All routes are JWT-protected using the Authorization header.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.schemas.pagination_schema import Page, PageMeta

from app.config import settings
from app import database
from app.schemas.task_schema import TaskCreate, TaskResponse

# -------------------------------------------------------------------
# Router configuration
# -------------------------------------------------------------------

# All task-related endpoints are grouped under /tasks
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# OAuth2 helper that extracts the Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -------------------------------------------------------------------
# Authentication dependency
# -------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Validate JWT access token and extract the username (subject).

    This function is used as a dependency in all protected routes.
    """
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
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


# -------------------------------------------------------------------
# Create new task
# -------------------------------------------------------------------
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    username: str = Depends(get_current_user),
):
    """
    Create a new task for the authenticated user.
    """
    new_task = {
        "_id": str(uuid.uuid4()),
        "title": task.title,
        "description": task.description,
        "owner": username,
        "created_at": datetime.utcnow(),
    }

    await database.db.tasks.insert_one(new_task)

    return TaskResponse(
        id=new_task["_id"],
        title=new_task["title"],
        description=new_task["description"],
        owner=new_task["owner"],
        created_at=new_task["created_at"],
    )


# -------------------------------------------------------------------
# List tasks (paginated)
# -------------------------------------------------------------------
@router.get("/", response_model=Page[TaskResponse])
async def get_tasks(
    username: str = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Return a paginated list of tasks belonging to the authenticated user.

    - limit: max number of tasks per page (1–100)
    - skip: number of tasks to skip (offset pagination)
    """
    cursor = (
        database.db.tasks.find({"owner": username})
        .sort("created_at", -1)  # Stable ordering for pagination
        .skip(skip)
        .limit(limit)
    )

    tasks = await cursor.to_list(length=limit)

    items = [
        TaskResponse(
            id=t["_id"],
            title=t["title"],
            description=t["description"],
            owner=t["owner"],
            created_at=t["created_at"],
        )
        for t in tasks
    ]

    has_more = len(items) == limit

    return Page(
        items=items,
        meta=PageMeta(
            limit=limit,
            has_more=has_more,
            next_cursor=None,  # offset pagination for now
        ),
    )


# -------------------------------------------------------------------
# Delete task
# -------------------------------------------------------------------
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    username: str = Depends(get_current_user),
):
    """
    Delete a task owned by the authenticated user.
    """
    result = await database.db.tasks.delete_one({"_id": task_id, "owner": username})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or unauthorized",
        )

    return None
