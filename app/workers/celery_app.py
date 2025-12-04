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
    """
    Initialize Mongo inside Celery worker safely.
    Handles cases where a loop already exists.
    """
    import asyncio

    async def _init():
        await connect_to_mongo()

    try:g
        # If Celery already has a running event loop (Redis backend)
        loop = asyncio.get_running_loop()
        loop.create_task(_init())   # schedule coroutine safely
    except RuntimeError:
        # No running loop: safe to call asyncio.run()
        asyncio.run(_init())

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
