"""ModelProvider model - represents an LLM API provider."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.models.model import Model


class ModelProvider(Base):
    """ModelProvider model - represents an LLM API provider.

    Attributes:
        id: UUID primary key
        name: Provider name (e.g., "OpenAI", "Anthropic")
        base_url: API base URL for the provider
        api_key: API key for the provider
        created_at: Timestamp when the provider was created
        updated_at: Timestamp when the provider was last updated
    """

    __tablename__ = "model_providers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(
        String(500),
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
        return f"<ModelProvider(id={self.id}, name={self.name})>"
