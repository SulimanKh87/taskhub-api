from celery import Celery                      # Celery handles distributed background tasks
from app.config import settings                # Load environment variables (broker URL, etc.)

# Create and configure a Celery instance named 'taskhub'
celery_app = Celery(
    "taskhub",                                 # Application name for Celery worker
    broker=settings.redis_broker,              # Redis URL used as the message broker
    backend=settings.redis_broker              # Redis also stores task results
)

# Update additional Celery configurations
celery_app.conf.update(
    task_serializer="json",                    # Serialize tasks in JSON format
    result_serializer="json",                  # Store results as JSON
    accept_content=["json"],                   # Only accept JSON tasks
    timezone="UTC",                            # Use Coordinated Universal Time
    enable_utc=True,                           # Ensures all times are in UTC
    worker_concurrency=2,                      # Number of concurrent worker threads
)

# Define a background task
@celery_app.task(autoretry_for=(Exception,), retry_backoff=True)
# autoretry_for → retries on exception
# retry_backoff=True → waits progressively longer between retries
def send_welcome_email(email: str):
    # Simulates sending a welcome email asynchronously
    print(f"Sending welcome email to: {email}")
    return {"status": "sent", "email": email}
