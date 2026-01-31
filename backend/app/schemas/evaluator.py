"""Evaluator schemas for API validation."""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class EvaluatorBase(BaseModel):
    """Base evaluator schema."""

    name: str = Field(..., min_length=1, max_length=100, description="评估器名称")
    description: Optional[str] = Field(None, description="评估器描述")
    type: Literal["llm_judge", "code"] = Field(..., description="评估器类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="评估器配置")


class EvaluatorCreate(EvaluatorBase):
    """Schema for creating an evaluator."""

    pass


class EvaluatorUpdate(BaseModel):
    """Schema for updating an evaluator."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class EvaluatorResponse(EvaluatorBase):
    """Schema for evaluator response."""

    id: str = Field(..., description="评估器ID")
    is_system: bool = Field(..., description="是否为系统内置评估器")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic config."""

        from_attributes = True


class TaskEvaluatorUpdate(BaseModel):
    """Schema for updating task evaluators."""

    evaluator_ids: list[str] = Field(..., description="按顺序排列的评估器ID列表")


class EvaluatorTestRequest(BaseModel):
    """Schema for testing an evaluator."""

    expected: str = Field(..., description="预期输出")
    actual: str = Field(..., description="实际输出")


class EvaluatorTestResponse(BaseModel):
    """Schema for evaluator test response."""

    result: str = Field(..., description="评估结果: passed 或 failed")
    reason: Optional[str] = Field(None, description="评估原因")
    error: Optional[str] = Field(None, description="错误信息")
