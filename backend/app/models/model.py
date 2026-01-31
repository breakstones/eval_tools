"""Model model - represents an LLM model available from a provider."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Model(Base):
    """Model model - represents an LLM model.

    Attributes:
        id: UUID primary key
        provider_id: Foreign key to ModelProvider
        model_code: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
        display_name: Human-readable name for the model
        created_at: Timestamp when the model was created
        updated_at: Timestamp when the model was last updated
    """

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    provider_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("model_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_code: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(200),
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

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, model_code={self.model_code}, display_name={self.display_name})>"
