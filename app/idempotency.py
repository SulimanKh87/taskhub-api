from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert  # IMPORTANT: PG insert for on_conflict

from app.models.job_log import JobLog


# ============================================================
# Idempotent Job Helpers (PostgreSQL)
# ============================================================

async def get_job_result(session: AsyncSession, job_id: str):
    """
    Return saved job result if job already completed.
    """
    stmt = select(JobLog).where(
        JobLog.job_id == job_id,
        JobLog.status == "completed",
    )
    res = await session.execute(stmt)
    job = res.scalar_one_or_none()
    return job.result if job else None


async def mark_job_started(session: AsyncSession, job_id: str) -> None:
    """
    Create job_log row if it doesn't exist (idempotent).
    Duplicate calls are ignored via ON CONFLICT DO NOTHING.

    NOTE: Do NOT commit here — tests/requests may manage the transaction scope.
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
    await session.flush()


async def save_job_result(session: AsyncSession, job_id: str, result: dict) -> None:
    """
    Persist a completed job result.

    NOTE: Do NOT commit here — tests/requests may manage the transaction scope.
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
    await session.flush()
