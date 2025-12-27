from datetime import datetime

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_log import JobLog


# ============================================================
# Idempotent Job Helpers (PostgreSQL)
# ============================================================

async def get_job_result(
    session: AsyncSession,
    job_id: str,
):
    """
    Return the saved job result if the job was already completed.

    Used by Celery tasks to short-circuit duplicate executions.
    """
    stmt = select(JobLog).where(
        JobLog.job_id == job_id,
        JobLog.status == "completed",
    )

    result = await session.execute(stmt)
    job = result.scalar_one_or_none()

    return job.result if job else None


async def mark_job_started(
    session: AsyncSession,
    job_id: str,
):
    """
    Mark a job as started in an idempotent way.

    This uses PostgreSQL's ON CONFLICT DO NOTHING to guarantee:
    - Only one row per job_id
    - Safe retries
    - No duplicate executions
    """
    stmt = (
        insert(JobLog)
        .values(
            job_id=job_id,
            status="in_progress",
            created_at=datetime.utcnow(),
        )
        .on_conflict_do_nothing(index_elements=["job_id"])
    )

    await session.execute(stmt)
    await session.commit()


async def save_job_result(
    session: AsyncSession,
    job_id: str,
    result: dict,
):
    """
    Save job result and mark job as completed.

    This updates the existing job_log row created during mark_job_started().
    """
    stmt = (
        update(JobLog)
        .where(JobLog.job_id == job_id)
        .values(
            status="completed",
            result=result,
            updated_at=datetime.utcnow(),
        )
    )

    await session.execute(stmt)
    await session.commit()
