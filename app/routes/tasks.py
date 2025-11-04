from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from datetime import datetime
from typing import List
from app.config import settings
from app.database import db
from app.schemas import TaskCreate, TaskResponse
import uuid

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ==========================
# Helper Function
# ==========================

async def get_current_user(token: str) -> str:
    """Decode and verify JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


# ==========================
# Create New Task
# ==========================

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, token: str):
    username = await get_current_user(token)

    new_task = {
        "_id": str(uuid.uuid4()),
        "title": task.title,
        "description": task.description,
        "owner": username,
        "created_at": datetime.utcnow(),
    }

    await db.tasks.insert_one(new_task)
    return TaskResponse(id=new_task["_id"], **task.dict(), created_at=new_task["created_at"])


# ==========================
# Get All Tasks
# ==========================

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(token: str):
    username = await get_current_user(token)
    cursor = db.tasks.find({"owner": username})
    tasks = await cursor.to_list(length=100)
    return [TaskResponse(id=t["_id"], title=t["title"], description=t["description"], owner=t["owner"], created_at=t["created_at"]) for t in tasks]


# ==========================
# Delete Task
# ==========================

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, token: str):
    username = await get_current_user(token)
    result = await db.tasks.delete_one({"_id": task_id, "owner": username})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
    return {"detail": "Task deleted"}
