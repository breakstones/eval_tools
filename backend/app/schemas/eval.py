"""Schemas for evaluation APIs."""

from datetime import datetime
from typing import Any, Optional, Dict, List

from pydantic import BaseModel, Field, ConfigDict


class RequestTemplate(BaseModel):
    """Schema for request template configuration."""

    model_config = ConfigDict(protected_namespaces=(), extra='allow')

    model: str = "${model_name}"
    messages: List[Dict[str, Any]] = []


class EvalTaskCreate(BaseModel):
    """Schema for creating an evaluation task."""

    model_config = ConfigDict(protected_namespaces=())

    set_id: str
    model_id: str
    concurrency: int = 1  # 并发数量，默认为1（串行）
    evaluator_types: List[str] = ["exact_match"]
    request_template: Optional[RequestTemplate] = None
    system_prompt: Optional[str] = None


class EvalTaskUpdate(BaseModel):
    """Schema for updating an evaluation task."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: Optional[str] = None
    concurrency: Optional[int] = None
    request_template: Optional[RequestTemplate] = None
    system_prompt: Optional[str] = None


class EvalTaskResponse(BaseModel):
    """Schema for evaluation task response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    set_id: str
    model_id: str
    concurrency: int = 1  # 并发数量
    request_template: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None  # 模型配置详情
    status: str
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class EvalResultResponse(BaseModel):
    """Schema for evaluation result response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    run_id: str
    task_id: str
    case_id: str
    case_uid: Optional[str] = None  # 用例编号，便于展示
    actual_output: Optional[str] = None
    is_passed: bool
    execution_error: Optional[str] = None  # 执行错误信息，如模型调用失败
    evaluator_logs: List[Any]
    created_at: datetime


class EvalRunResponse(BaseModel):
    """Schema for evaluation run response."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    task_id: str
    run_number: int
    status: str
    summary: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class EvalProgressEvent(BaseModel):
    """Schema for SSE progress event."""

    type: str
    data: Dict[str, Any]


class EvalSummary(BaseModel):
    """Schema for evaluation summary."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0


class TemplateTestRequest(BaseModel):
    """Schema for testing request template."""

    case_id: Optional[str] = None
    test_input: Optional[str] = None


class TemplateTestResponse(BaseModel):
    """Schema for template test response."""

    rendered_request: Dict[str, Any]
    actual_response: Optional[str] = None
    error: Optional[str] = None
