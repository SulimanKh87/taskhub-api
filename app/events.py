# app/events.py
import json
import boto3
from app.config import settings


def publish_task_created(task_id: str, task_title: str, owner: str) -> None:
    if settings.app_env != "prod":
        return

    try:
        client = boto3.client(
            "events",
            region_name=settings.aws_region,
        )

        client.put_events(
            Entries=[
                {
                    "EventBusName": settings.event_bus_name,
                    "Source": "taskhub.api",
                    "DetailType": "TaskCreated",
                    "Detail": json.dumps(
                        {
                            "task_id": task_id,
                            "task_title": task_title,
                            "owner": owner,
                        }
                    ),
                }
            ]
        )
    except Exception as e:
        print(f"Failed to publish TaskCreated event: {e}")
