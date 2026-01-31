"""TaskEvaluator model - association between tasks and evaluators."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.eval_task import EvalTask
    from app.models.evaluator import Evaluator


class TaskEvaluator(Base):
    """TaskEvaluator model - association between evaluation tasks and evaluators.

    Attributes:
        id: UUID primary key
        task_id: Foreign key to EvalTask
        evaluator_id: Foreign key to Evaluator
        order_index: Execution order for evaluators
    """

    __tablename__ = "task_evaluators"

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
    evaluator_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evaluators.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    task: Mapped["EvalTask"] = relationship(
        "EvalTask",
        back_populates="task_evaluators",
    )
    evaluator: Mapped["Evaluator"] = relationship(
        "Evaluator",
    )

    def __repr__(self) -> str:
        return f"<TaskEvaluator(id={self.id}, task_id={self.task_id}, evaluator_id={self.evaluator_id})>"
