from celery import Celery
from app.config import settings

celery_app = Celery(
    "taskhub",
    broker=settings.redis_broker,
    backend=settings.redis_broker
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
)

@celery_app.task(autoretry_for=(Exception,), retry_backoff=True)
def send_welcome_email(email: str):
    print(f"Sending welcome email to: {email}")
    return {"status": "sent", "email": email}
