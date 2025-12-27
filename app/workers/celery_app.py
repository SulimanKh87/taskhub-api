"""
celery_app.py

This module should ONLY:
- Create the Celery instance
- Register task modules

Database access is handled lazily inside tasks using SQLAlchemy sessions.
"""

from celery import Celery
from celery.signals import worker_process_init

from app.config import settings


# ------------------------------------------------------------
# Celery Setup
# ------------------------------------------------------------
celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker,
)

# Register Celery task modules
celery_app.conf.imports = (
    "app.workers.tasks.email_tasks",
)

# Celery runtime configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)


@worker_process_init.connect
def init_worker(**_kwargs):
    """
    Worker initialization hook.

    No database connections are created here.
    SQLAlchemy sessions are created lazily per task.
    """
    pass
