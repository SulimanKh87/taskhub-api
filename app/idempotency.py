from datetime import datetime

from app.database import db


async def get_job_result(job_id: str):
    """Return the saved job result if the job is already completed."""
    return await db.job_log.find_one({"job_id": job_id, "status": "completed"})


async def mark_job_started(job_id: str):
    """Mark a job as started in an idempotent way (insert only once)."""
    await db.job_log.update_one(
        {"job_id": job_id},
        {
            "$setOnInsert": {
                "job_id": job_id,
                "status": "in_progress",
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


async def save_job_result(job_id: str, result: dict):
    """Save job result and mark job as completed."""
    await db.job_log.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "completed",
                "result": result,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )
