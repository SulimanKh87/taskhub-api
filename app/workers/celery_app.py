"""celery_app.py should ONLY create Celery instance & import tasks."""

# ------------------------------------------------------------
# Celery Setup
# ------------------------------------------------------------
from celery import Celery

from app.config import settings

from celery.signals import worker_process_init
from app.database import connect_to_mongo


# Create Celery app
celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker,
)

# Register tasks module
celery_app.conf.imports = (
    "app.workers.tasks.email_tasks",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)


@worker_process_init.connect
def init_celery_mongo(**_kwargs):
    """Ensure MongoDB is connected inside Celery worker processes."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(connect_to_mongo())
    except RuntimeError:
        # No running loop → create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connect_to_mongo())
