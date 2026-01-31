"""EvalTask model - represents an evaluation task."""

import json
import uuid
from datetime import datetime
from typing import Any, Optional, Dict

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvalTask(Base):
    """EvalTask model - represents an evaluation task for a case set.

    Attributes:
        id: UUID primary key
        set_id: Foreign key to CaseSet being evaluated
        model_id: Foreign key to Model (selected LLM model)
        request_template: JSON string containing request template configuration
        status: Task status (PENDING, RUNNING, COMPLETED, FAILED)
        summary: JSON string containing execution summary (total, passed, failed)
        created_at: Timestamp when the task was created
        updated_at: Timestamp when the task was last updated
    """

    __tablename__ = "eval_tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    set_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("case_sets.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
    )
    concurrency: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    request_template: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @property
    def request_template_dict(self) -> Dict[str, Any]:
        """Parse request_template JSON string to dict."""
        return json.loads(self.request_template)

    @request_template_dict.setter
    def request_template_dict(self, value: Dict[str, Any]) -> None:
        """Set request_template from dict."""
        self.request_template = json.dumps(value)

    @property
    def summary_dict(self) -> Optional[Dict[str, Any]]:
        """Parse summary JSON string to dict."""
        if self.summary is None:
            return None
        return json.loads(self.summary)

    @summary_dict.setter
    def summary_dict(self, value: Optional[Dict[str, Any]]) -> None:
        """Set summary from dict."""
        self.summary = json.dumps(value) if value else None

    def __repr__(self) -> str:
        return f"<EvalTask(id={self.id}, status={self.status})>"
