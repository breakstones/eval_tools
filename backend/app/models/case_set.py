"""CaseSet model - represents a collection of test cases."""

import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaseSet(Base):
    """CaseSet model - represents a collection of test cases.

    Attributes:
        id: UUID primary key
        name: Name of the case set
        created_at: Timestamp when the case set was created
    """

    __tablename__ = "case_sets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CaseSet(id={self.id}, name={self.name})>"
