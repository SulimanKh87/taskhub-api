import asyncio
from datetime import datetime

from celery import Celery  # Celery handles distributed background tasks

from app.config import settings  # Load environment variables (broker URL, etc.)
from app.idempotency import get_job_result, mark_job_started, save_job_result

# Create and configure a Celery instance named 'taskhub'
celery_app = Celery(
    "taskhub",  # Application name for Celery worker
    broker=settings.redis_broker,  # Redis URL used as the message broker
    backend=settings.redis_broker,  # Redis also stores task results
)

# IMPORT tasks explicitly so Celery registers them
celery_app.conf.imports = ("app.tasks",)

# Update additional Celery configurations
celery_app.conf.update(
    task_serializer="json",  # Serialize tasks in JSON format
    result_serializer="json",  # Store results as JSON
    accept_content=["json"],  # Only accept JSON tasks
    timezone="UTC",  # Use Coordinated Universal Time
    enable_utc=True,  # Ensures all times are in UTC
    worker_concurrency=2,  # Number of concurrent worker threads
)


# Define a background task
# autoretry_for → retries on exception
# retry_backoff=True → waits progressively longer between retries
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True,
    name="taskhub.send_welcome_email",)
def send_welcome_email(self, email: str, job_id: str):
    """
    Idempotent Celery email task.
    job_id must be UNIQUE for every logical email.
    """

    loop = asyncio.get_event_loop()

    # Step 1 — check if already processed
    existing = loop.run_until_complete(get_job_result(job_id))
    if existing:
        return existing["result"]

    # Step 2 — mark as started
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
