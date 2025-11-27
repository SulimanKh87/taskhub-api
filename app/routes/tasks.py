# Manages CRUD operations for tasks — protected by JWT authentication

import uuid  # Used for generating unique task IDs
from datetime import datetime  # For timestamps
from typing import List  # For defining response type hints

from fastapi import APIRouter, HTTPException, status  # FastAPI tools for building routes and error handling
from jose import jwt, JWTError  # For decoding and validating JWT tokens

from app.config import settings  # Load app configuration
from app.database import db  # MongoDB connection
from app.schemas import TaskCreate, TaskResponse  # Pydantic schemas for validation

# Define router for all /tasks routes
router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ==========================
# Helper Function
# ==========================

async def get_current_user(token: str) -> str:
    """Decode and verify JWT."""
    # If token is invalid or expired, raise 401 Unauthorized
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT to extract the username
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")  # The “sub” claim holds username
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        # Token verification failed
        raise credentials_exception


# ==========================
# Create New Task
# ==========================

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, token: str):
    # Decode token and get the username of the current user
    username = await get_current_user(token)

    # Build the task document
    new_task = {
        "_id": str(uuid.uuid4()),
        "title": task.title,
        "description": task.description,
        "owner": username,
        "created_at": datetime.utcnow(),
    }

    # Save to MongoDB
    await db.tasks.insert_one(new_task)

    # Return a Pydantic-validated response
    return TaskResponse(id=new_task["_id"], **task.dict(), created_at=new_task["created_at"])


# ==========================
# Get All Tasks
# ==========================

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(token: str):
    # Verify user identity from token
    username = await get_current_user(token)

    # Retrieve all tasks belonging to this user
    cursor = db.tasks.find({"owner": username})
    tasks = await cursor.to_list(length=100)  # Limit to 100 results

    # Convert raw MongoDB documents to TaskResponse models
    return [
        TaskResponse(
            id=t["_id"],
            title=t["title"],
            description=t["description"],
            owner=t["owner"],
            created_at=t["created_at"]
        )
        for t in tasks
    ]


# ==========================
# Delete Task
# ==========================

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, token: str):
    # Verify who is deleting
    username = await get_current_user(token)

    # Delete only if the task belongs to this user
    result = await db.tasks.delete_one({"_id": task_id, "owner": username})

    # Handle not found or unauthorized attempts
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    return {"detail": "Task deleted"}
