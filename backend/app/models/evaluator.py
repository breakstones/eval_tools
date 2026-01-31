"""Evaluator model - represents an evaluator configuration."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING, List

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task_evaluator import TaskEvaluator


class Evaluator(Base):
    """Evaluator model - represents an evaluator configuration.

    Attributes:
        id: UUID primary key
        name: Evaluator name (unique)
        description: Evaluator description
        type: Evaluator type (llm_judge or code)
        config: JSON configuration (prompt template or code)
        is_system: Whether this is a system built-in evaluator
        created_at: Timestamp when the evaluator was created
        updated_at: Timestamp when the evaluator was last updated
    """

    __tablename__ = "evaluators"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    config: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )
    is_system: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
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
    def config_dict(self) -> Dict[str, Any]:
        """Parse config JSON string to dict."""
        try:
            return json.loads(self.config)
        except json.JSONDecodeError:
            return {}

    @config_dict.setter
    def config_dict(self, value: Dict[str, Any]) -> None:
        """Set config from dict."""
        self.config = json.dumps(value, ensure_ascii=False)

    # Relationships
    task_evaluators: Mapped[List["TaskEvaluator"]] = relationship(
        "TaskEvaluator",
        back_populates="evaluator",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Evaluator(id={self.id}, name={self.name}, type={self.type})>"
