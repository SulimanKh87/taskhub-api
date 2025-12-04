from celery import Celery
from app.config import settings
from app.database import connect_to_mongo

# ------------------------------------------------------------
# Create Celery Application
# ------------------------------------------------------------
celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker,
)


# ------------------------------------------------------------
# Ensure MongoDB is connected in Celery worker process
# ------------------------------------------------------------
# IMPORTANT: connect to Mongo when worker starts
@celery_app.on_after_configure.connect
def init_mongo_connection(sender, **kwargs):
    import asyncio

    asyncio.run(connect_to_mongo())


# ------------------------------------------------------------
# Celery Configuration
# ------------------------------------------------------------
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)

# ------------------------------------------------------------
# Import REAL tasks module
# ------------------------------------------------------------
# IMPORTANT:
# We now import the dedicated tasks file, NOT celery_app.py itself.
celery_app.conf.imports = ("app.workers.tasks",)
