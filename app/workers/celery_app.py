import asyncio
from datetime import datetime

from celery import Celery

from app.config import settings
from app.database import connect_to_mongo
from app.idempotency import get_job_result, mark_job_started, save_job_result


# ------------------------------------------------------------
# Celery Application Setup
# ------------------------------------------------------------
celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker,
)

# Celery must import the tasks module to register tasks
celery_app.conf.imports = ("app.workers.celery_tasks",)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)


# ------------------------------------------------------------
# Celery Task (Idempotent welcome email)
# ------------------------------------------------------------
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    name="taskhub.send_welcome_email",
)
def send_welcome_email(self, email: str, job_id: str):
    """
    Idempotent Celery task.
    Uses its own fresh event loop per invocation.
    """

    # Each Celery worker thread needs its own loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Step 1 — check if already processed
    existing = loop.run_until_complete(get_job_result(job_id))
    if existing:
        return existing["result"]

    # Step 2 — mark as started
    loop.run_until_complete(mark_job_started(job_id))

    # Step 3 — main logic
    result = {
        "status": "sent",
        "email": email,
        "processed_at": datetime.utcnow().isoformat(),
    }

    # Step 4 — save result
    loop.run_until_complete(save_job_result(job_id, result))

    return result
