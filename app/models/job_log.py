# app/models/job_log.py

from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobLog(Base):
    """
    Stores background job execution state.

    Guarantees idempotent execution by enforcing a single row per job_id.
    """

    __tablename__ = "job_log"

    job_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,  # idempotency guarantee
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
