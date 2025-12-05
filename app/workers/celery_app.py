"""  celery_app.py should ONLY create Celery instance & import tasks. """

# ------------------------------------------------------------
# Celery Setup
# ------------------------------------------------------------
from celery import Celery

from app.config import settings
from app.workers.tasks import _send  # noqa: F401

# Create Celery app
celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker,
)

# Register tasks module
celery_app.conf.imports = ("app.workers.tasks",)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)

# ------------------------------------------------------------
# Import tasks so Celery registers them
# ------------------------------------------------------------
"""
Why import at the BOTTOM?
Because:
Celery must finish initializing celery_app first
THEN load tasks — otherwise circular import occurs
Ruff allows # noqa: F401 meaning “unused import is intentional”
A bottom import avoids:
Circular dependencies
Celery failing to discover tasks
Python loading celery_app twice
"""
