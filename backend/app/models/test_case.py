"""TestCase model - represents a single test case."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestCase(Base):
    """TestCase model - represents a single test case within a case set.

    Attributes:
        id: UUID primary key
        set_id: Foreign key to CaseSet
        case_uid: User-visible case identifier (e.g., CASE-001)
        description: Description of what the test case validates
        user_input: The user prompt to test
        expected_output: Expected output for comparison
        created_at: Timestamp when the test case was created
    """

    __tablename__ = "test_cases"

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
    case_uid: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, case_uid={self.case_uid})>"
