"""Schemas for case management APIs."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CaseSetBase(BaseModel):
    """Base schema for CaseSet."""

    name: str = Field(..., min_length=1, max_length=255, description="用例集名称")


class CaseSetCreate(CaseSetBase):
    """Schema for creating a CaseSet."""

    pass


class CaseSetUpdate(CaseSetBase):
    """Schema for updating a CaseSet."""

    name: Optional[str] = None


class CaseSetResponse(CaseSetBase):
    """Schema for CaseSet response."""

    id: str
    created_at: datetime
    case_count: int = 0

    model_config = {"from_attributes": True}


class TestCaseBase(BaseModel):
    """Base schema for TestCase."""

    case_uid: Optional[str] = Field(None, max_length=50, description="用例编号")
    description: Optional[str] = Field(None, max_length=255, description="用例描述")
    user_input: str = Field(..., min_length=1, description="用户输入")
    expected_output: Optional[str] = Field(None, description="预期输出")


class TestCaseCreate(TestCaseBase):
    """Schema for creating a TestCase."""

    set_id: str = Field(..., description="所属用例集ID")


class TestCaseUpdate(TestCaseBase):
    """Schema for updating a TestCase."""

    user_input: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    """Schema for TestCase response."""

    id: str
    set_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExcelImportResponse(BaseModel):
    """Schema for Excel import response."""

    case_set: CaseSetResponse
    cases_created: int


class ExcelRowData(BaseModel):
    """Schema for a single row in Excel import."""

    case_uid: Optional[str] = None
    description: Optional[str] = None
    user_input: str
    expected_output: Optional[str] = None
