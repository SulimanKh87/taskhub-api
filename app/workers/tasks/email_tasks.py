import asyncio
from datetime import datetime

from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="taskhub.send_welcome_email",
)
def send_welcome_email(self, email: str, job_id: str):
    """
    Idempotent Celery welcome email task.
    Runs async DB checks inside a synchronous Celery worker.
    """

    # Local import prevents circular import with celery_app
    from app.idempotency import (
        get_job_result,
        mark_job_started,
        save_job_result,
    )

    # Get or create event loop (Celery workers are synchronous)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Step 1 — idempotency check
    existing = loop.run_until_complete(get_job_result(job_id))
    if existing:
        return existing["result"]

    # Step 2 — mark started
    loop.run_until_complete(mark_job_started(job_id))

    # Step 3 — actual logic
    result = {
        "status": "sent",
        "email": email,
        "processed_at": datetime.utcnow().isoformat(),
    }

    # Step 4 — save result
    loop.run_until_complete(save_job_result(job_id, result))

    return result
