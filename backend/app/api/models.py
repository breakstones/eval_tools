"""API routes for model and provider management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_model_service
from app.schemas.models import (
    ModelCreate,
    ModelProviderCreate,
    ModelProviderResponse,
    ModelProviderUpdate,
    ModelResponse,
    ModelUpdate,
)
from app.services.model_service import ModelService

router = APIRouter(prefix="/api/models", tags=["models"])


# Provider endpoints
@router.get("/providers", response_model=list[ModelProviderResponse])
async def get_providers(
    service: ModelService = Depends(get_model_service),
) -> list[ModelProviderResponse]:
    """Get all model providers."""
    providers = await service.get_providers()

    # Get model count for each provider
    result = []
    for provider in providers:
        models = await service.get_models(provider.id)
        result.append(ModelProviderResponse(
            id=provider.id,
            name=provider.name,
            base_url=provider.base_url,
            api_key=provider.api_key,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
            models_count=len(models),
        ))
    return result


@router.get("/providers/{provider_id}", response_model=ModelProviderResponse)
async def get_provider(
    provider_id: str,
    service: ModelService = Depends(get_model_service),
) -> ModelProviderResponse:
    """Get a model provider by ID."""
    provider = await service.get_provider(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="模型提供方不存在")

    models = await service.get_models(provider_id)
    return ModelProviderResponse(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        api_key=provider.api_key,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        models_count=len(models),
    )


@router.post("/providers", response_model=ModelProviderResponse, status_code=201)
async def create_provider(
    data: ModelProviderCreate,
    service: ModelService = Depends(get_model_service),
) -> ModelProviderResponse:
    """Create a new model provider."""
    try:
        provider = await service.create_provider(data.name, data.base_url, data.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ModelProviderResponse(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        api_key=provider.api_key,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        models_count=0,
    )


@router.put("/providers/{provider_id}", response_model=ModelProviderResponse)
async def update_provider(
    provider_id: str,
    data: ModelProviderUpdate,
    service: ModelService = Depends(get_model_service),
) -> ModelProviderResponse:
    """Update a model provider."""
    try:
        provider = await service.update_provider(provider_id, **data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    models = await service.get_models(provider_id)
    return ModelProviderResponse(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        api_key=provider.api_key,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        models_count=len(models),
    )


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    service: ModelService = Depends(get_model_service),
) -> None:
    """Delete a model provider."""
    deleted = await service.delete_provider(provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="模型提供方不存在")


# Model endpoints
@router.get("/models", response_model=list[ModelResponse])
async def get_models(
    provider_id: Optional[str] = None,
    service: ModelService = Depends(get_model_service),
) -> list[ModelResponse]:
    """Get all models, optionally filtered by provider."""
    models_data = await service.get_models(provider_id)
    return [
        ModelResponse(
            id=m["id"],
            provider_id=m["provider_id"],
            model_code=m["model_code"],
            display_name=m["display_name"],
            provider_name=m["provider_name"],
            provider_base_url=m["provider_base_url"],
            created_at=m["created_at"],
            updated_at=m["updated_at"],
        )
        for m in models_data
    ]


@router.get("/models/{model_id}", response_model=dict)
async def get_model(
    model_id: str,
    service: ModelService = Depends(get_model_service),
) -> dict:
    """Get a model by ID with provider details."""
    model = await service.get_model(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(
    data: ModelCreate,
    service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """Create a new model."""
    try:
        model = await service.create_model(data.provider_id, data.model_code, data.display_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    provider = await service.get_provider(data.provider_id)
    return ModelResponse(
        id=model.id,
        provider_id=model.provider_id,
        model_code=model.model_code,
        display_name=model.display_name,
        provider_name=provider.name,
        provider_base_url=provider.base_url,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    data: ModelUpdate,
    service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """Update a model."""
    try:
        model = await service.update_model(model_id, **data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    provider = await service.get_provider(model.provider_id)
    return ModelResponse(
        id=model.id,
        provider_id=model.provider_id,
        model_code=model.model_code,
        display_name=model.display_name,
        provider_name=provider.name,
        provider_base_url=provider.base_url,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    service: ModelService = Depends(get_model_service),
) -> None:
    """Delete a model."""
    deleted = await service.delete_model(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="模型不存在")
