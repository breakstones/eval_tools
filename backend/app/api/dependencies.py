"""Dependency functions for API routes."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.case_service import CaseService
from app.services.eval_service import EvalService
from app.services.excel_service import ExcelService
from app.services.model_service import ModelService


async def get_case_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[CaseService, None]:
    """Get case service instance.

    Yields:
        CaseService instance
    """
    service = CaseService(db)
    yield service


async def get_excel_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ExcelService, None]:
    """Get Excel service instance.

    Yields:
        ExcelService instance
    """
    service = ExcelService(db)
    # Initialize case service reference
    service.case_service = CaseService(db)
    yield service


async def get_eval_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[EvalService, None]:
    """Get evaluation service instance.

    Yields:
        EvalService instance
    """
    service = EvalService(db)
    yield service


async def get_model_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ModelService, None]:
    """Get model service instance.

    Yields:
        ModelService instance
    """
    service = ModelService(db)
    yield service
