from datetime import datetime

from app.idempotency import get_job_result, mark_job_started, save_job_result
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="taskhub.send_welcome_email",
)
async def _send(email: str, job_id: str):
    # Step 1 — idempotency check
    existing = await get_job_result(job_id)
    if existing:
        return existing["result"]

    # Step 2 — mark start
    await mark_job_started(job_id)

    # Step 3 — logic
    result = {
        "status": "sent",
        "email": email,
        "processed_at": datetime.utcnow().isoformat(),
    }

    # Step 4 — save
    await save_job_result(job_id, result)
    return result
