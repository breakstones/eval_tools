"""EvalRun model - tracks each execution run of an evaluation task."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvalRun(Base):
    """EvalRun model - represents a single execution run of an evaluation task.

    Attributes:
        id: UUID primary key
        task_id: Foreign key to EvalTask
        run_number: The run number (1, 2, 3, ...)
        status: Run status (PENDING, RUNNING, COMPLETED, FAILED)
        summary: JSON string containing execution summary
        started_at: Timestamp when the run started
        completed_at: Timestamp when the run completed
        error: Error message if the run failed
    """

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eval_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        nullable=True,
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<EvalRun(id={self.id}, task_id={self.task_id}, run_number={self.run_number})>"
