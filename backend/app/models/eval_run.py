"""EvalRun model - tracks each execution run of an evaluation task."""

import uuid
import json
from datetime import datetime
from typing import Optional, Any, Dict

from sqlalchemy import ForeignKey, String, Text, Integer
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
        total_duration_ms: Total execution duration in milliseconds (completed_at - started_at)
        total_skill_tokens: Total skill LLM tokens consumed across all cases
        total_evaluator_tokens: Total evaluator LLM tokens consumed across all cases
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
    total_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total execution duration in milliseconds (completed_at - started_at)",
    )
    total_skill_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total skill LLM tokens consumed across all cases",
    )
    total_evaluator_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total evaluator LLM tokens consumed across all cases",
    )

    @property
    def summary_dict(self) -> Dict[str, Any]:
        """Parse summary JSON string to dict."""
        if not self.summary:
            return {}
        return json.loads(self.summary)

    @summary_dict.setter
    def summary_dict(self, value: Dict[str, Any]) -> None:
        """Set summary from dict."""
        self.summary = json.dumps(value)

    def __repr__(self) -> str:
        return f"<EvalRun(id={self.id}, task_id={self.task_id}, run_number={self.run_number})>"
