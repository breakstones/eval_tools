"""EvalResult model - represents evaluation result for a single test case."""

import json
import uuid
from typing import Any, List, Dict, Optional

from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvalResult(Base):
    """EvalResult model - represents evaluation result for a single test case.

    Attributes:
        id: UUID primary key
        run_id: Foreign key to EvalRun (tracks which execution run this result belongs to)
        task_id: Foreign key to EvalTask (kept for backward compatibility)
        case_id: Foreign key to TestCase
        actual_output: Actual output from the LLM
        is_passed: Whether the test case passed evaluation
        evaluator_logs: JSON string containing logs from each evaluator
        created_at: Timestamp when the result was created
    """

    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eval_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    execution_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 执行错误信息
    evaluator_logs: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    @property
    def evaluator_logs_list(self) -> List[Dict[str, Any]]:
        """Parse evaluator_logs JSON string to list."""
        return json.loads(self.evaluator_logs)

    @evaluator_logs_list.setter
    def evaluator_logs_list(self, value: List[Dict[str, Any]]) -> None:
        """Set evaluator_logs from list."""
        self.evaluator_logs = json.dumps(value)

    def __repr__(self) -> str:
        return f"<EvalResult(id={self.id}, is_passed={self.is_passed})>"
