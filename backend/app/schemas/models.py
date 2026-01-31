"""Schemas for model management APIs."""

from datetime import datetime
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field, ConfigDict


class ModelProviderCreate(BaseModel):
    """Schema for creating a model provider."""

    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key: str = Field(..., min_length=1, max_length=500)


class ModelProviderUpdate(BaseModel):
    """Schema for updating a model provider."""

    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = Field(None, min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, min_length=1, max_length=500)


class ModelProviderResponse(BaseModel):
    """Schema for model provider response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    name: str
    base_url: str
    api_key: str  # Note: In production, you may want to mask this
    created_at: datetime
    updated_at: datetime
    models_count: int = 0  # Will be populated from query


class ModelCreate(BaseModel):
    """Schema for creating a model."""

    model_config = ConfigDict(protected_namespaces=())

    provider_id: str
    model_code: str = Field(..., min_length=1, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=200)


class ModelUpdate(BaseModel):
    """Schema for updating a model."""

    model_config = ConfigDict(protected_namespaces=())

    model_code: Optional[str] = Field(None, min_length=1, max_length=200)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)


class ModelResponse(BaseModel):
    """Schema for model response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    provider_id: str
    model_code: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    provider_name: str = ""  # Will be populated from join
    provider_base_url: str = ""  # Will be populated from join


class ModelWithProviderResponse(BaseModel):
    """Schema for model with provider details."""

    model_config = ConfigDict(protected_namespaces=())

    id: str
    provider_id: str
    model_code: str
    display_name: str
    provider: ModelProviderResponse
