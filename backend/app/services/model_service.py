"""Service for model and provider management."""

from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.model import Model
from app.models.model_provider import ModelProvider


class ModelService:
    """Service for managing model providers and models."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Database session
        """
        self.session = session

    @classmethod
    async def create(cls, session: AsyncSession):
        """Create a new service instance."""
        return cls(session)

    # Provider methods
    async def get_providers(self) -> List[ModelProvider]:
        """Get all model providers."""
        result = await self.session.execute(
            select(ModelProvider).order_by(ModelProvider.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_provider(self, provider_id: str) -> Optional[ModelProvider]:
        """Get a provider by ID."""
        result = await self.session.execute(
            select(ModelProvider).where(ModelProvider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def create_provider(self, name: str, base_url: str, api_key: str) -> ModelProvider:
        """Create a new model provider."""
        # Check if name already exists
        existing = await self.session.execute(
            select(ModelProvider).where(ModelProvider.name == name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"提供方名称已存在: {name}")

        provider = ModelProvider(name=name, base_url=base_url, api_key=api_key)
        self.session.add(provider)
        await self.session.flush()
        await self.session.refresh(provider)
        return provider

    async def update_provider(self, provider_id: str, **kwargs) -> ModelProvider:
        """Update a model provider."""
        provider = await self.get_provider(provider_id)
        if provider is None:
            raise ValueError(f"提供方不存在: {provider_id}")

        # Check name uniqueness if updating name
        if "name" in kwargs and kwargs["name"] != provider.name:
            existing = await self.session.execute(
                select(ModelProvider).where(ModelProvider.name == kwargs["name"])
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"提供方名称已存在: {kwargs['name']}")

        for key, value in kwargs.items():
            setattr(provider, key, value)

        await self.session.flush()
        await self.session.refresh(provider)
        return provider

    async def delete_provider(self, provider_id: str) -> bool:
        """Delete a model provider and all its models."""
        provider = await self.get_provider(provider_id)
        if provider is None:
            return False

        # Delete all models for this provider (cascade should handle this)
        await self.session.execute(delete(Model).where(Model.provider_id == provider_id))

        # Delete provider
        await self.session.execute(delete(ModelProvider).where(ModelProvider.id == provider_id))
        return True

    # Model methods
    async def get_models(self, provider_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all models, optionally filtered by provider."""
        query = select(Model, ModelProvider).join(
            ModelProvider, Model.provider_id == ModelProvider.id
        ).order_by(ModelProvider.name, Model.display_name)

        if provider_id:
            query = query.where(Model.provider_id == provider_id)

        result = await self.session.execute(query)
        models_data = []
        for model, provider in result.all():
            models_data.append({
                "id": model.id,
                "provider_id": model.provider_id,
                "model_code": model.model_code,
                "display_name": model.display_name,
                "provider_name": provider.name,
                "provider_base_url": provider.base_url,
                "created_at": model.created_at,
                "updated_at": model.updated_at,
            })
        return models_data

    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a model by ID with provider details."""
        result = await self.session.execute(
            select(Model, ModelProvider).join(
                ModelProvider, Model.provider_id == ModelProvider.id
            ).where(Model.id == model_id)
        )
        row = result.first()
        if row is None:
            return None

        model, provider = row
        return {
            "id": model.id,
            "provider_id": model.provider_id,
            "model_code": model.model_code,
            "display_name": model.display_name,
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "base_url": provider.base_url,
                "api_key": provider.api_key,
                "created_at": provider.created_at,
                "updated_at": provider.updated_at,
            },
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_model(self, provider_id: str, model_code: str, display_name: str) -> Model:
        """Create a new model."""
        # Verify provider exists
        provider = await self.get_provider(provider_id)
        if provider is None:
            raise ValueError(f"提供方不存在: {provider_id}")

        # Check for duplicate model_code in the same provider
        existing = await self.session.execute(
            select(Model).where(
                Model.provider_id == provider_id,
                Model.model_code == model_code
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"该提供方下已存在模型代码: {model_code}")

        model = Model(
            provider_id=provider_id,
            model_code=model_code,
            display_name=display_name,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def update_model(self, model_id: str, **kwargs) -> Model:
        """Update a model."""
        result = await self.session.execute(
            select(Model).where(Model.id == model_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"模型不存在: {model_id}")

        for key, value in kwargs.items():
            setattr(model, key, value)

        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        result = await self.session.execute(
            select(Model).where(Model.id == model_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self.session.execute(delete(Model).where(Model.id == model_id))
        return True
