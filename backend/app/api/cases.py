"""API routes for case set and test case management."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_case_service, get_excel_service
from app.database import get_db
from app.schemas.cases import (
    CaseSetCreate,
    CaseSetResponse,
    CaseSetUpdate,
    ExcelImportResponse,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseUpdate,
)
from app.services.case_service import CaseService
from app.services.excel_service import ExcelService

router = APIRouter(prefix="/api/cases", tags=["cases"])


# Case Set endpoints
@router.get("/sets", response_model=list[CaseSetResponse])
async def get_case_sets(
    service: CaseService = Depends(get_case_service),
) -> list[CaseSetResponse]:
    """Get all case sets."""
    case_sets = await service.get_case_sets()
    result = []
    for cs in case_sets:
        count = await service.get_case_count(cs.id)
        result.append(CaseSetResponse(
            id=cs.id,
            name=cs.name,
            created_at=cs.created_at,
            case_count=count,
        ))
    return result


@router.get("/sets/{case_set_id}", response_model=CaseSetResponse)
async def get_case_set(
    case_set_id: str,
    service: CaseService = Depends(get_case_service),
) -> CaseSetResponse:
    """Get a case set by ID."""
    case_set = await service.get_case_set(case_set_id)
    if case_set is None:
        raise HTTPException(status_code=404, detail="用例集不存在")
    count = await service.get_case_count(case_set_id)
    return CaseSetResponse(
        id=case_set.id,
        name=case_set.name,
        created_at=case_set.created_at,
        case_count=count,
    )


@router.post("/sets", response_model=CaseSetResponse, status_code=201)
async def create_case_set(
    data: CaseSetCreate,
    service: CaseService = Depends(get_case_service),
) -> CaseSetResponse:
    """Create a new case set."""
    case_set = await service.create_case_set(data)
    return CaseSetResponse(
        id=case_set.id,
        name=case_set.name,
        created_at=case_set.created_at,
        case_count=0,
    )


@router.put("/sets/{case_set_id}", response_model=CaseSetResponse)
async def update_case_set(
    case_set_id: str,
    data: CaseSetUpdate,
    service: CaseService = Depends(get_case_service),
) -> CaseSetResponse:
    """Update a case set."""
    case_set = await service.update_case_set(case_set_id, data)
    if case_set is None:
        raise HTTPException(status_code=404, detail="用例集不存在")
    count = await service.get_case_count(case_set_id)
    return CaseSetResponse(
        id=case_set.id,
        name=case_set.name,
        created_at=case_set.created_at,
        case_count=count,
    )


@router.delete("/sets/{case_set_id}", status_code=204)
async def delete_case_set(
    case_set_id: str,
    service: CaseService = Depends(get_case_service),
) -> None:
    """Delete a case set and all its test cases."""
    deleted = await service.delete_case_set(case_set_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="用例集不存在")


@router.get("/sets/{case_set_id}/export")
async def export_case_set(
    case_set_id: str,
    service: ExcelService = Depends(get_excel_service),
) -> Response:
    """Export a case set to Excel."""
    excel_data = await service.export_excel(case_set_id)
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cases.xlsx"},
    )


@router.post("/import", response_model=ExcelImportResponse, status_code=201)
async def import_excel(
    file: UploadFile,
    set_id: Optional[str] = Query(None, description="Case set ID to append cases to"),
    service: ExcelService = Depends(get_excel_service),
    case_service: CaseService = Depends(get_case_service),
) -> ExcelImportResponse:
    """Import case set and test cases from Excel file.

    Args:
        file: Excel file to import
        set_id: Optional case set ID to append to. If provided, cases will be
               imported to the existing set with deduplication by case_uid.
    """
    print(f"[DEBUG] import_excel called with set_id={set_id}")
    content = await file.read()
    try:
        if set_id:
            # Append to existing case set with deduplication
            print(f"[DEBUG] Importing to existing set: {set_id}")
            case_set = await case_service.get_case_set(set_id)
            if case_set is None:
                raise HTTPException(status_code=404, detail="用例集不存在")
            test_cases = await service.import_to_set(content, case_set)
            cases_created = len(test_cases)
            print(f"[DEBUG] Imported {cases_created} cases to set {set_id}")
        else:
            # Create new case set
            print(f"[DEBUG] Creating new case set")
            case_set, test_cases = await service.import_excel(content, file.filename)
            cases_created = len(test_cases)
            print(f"[DEBUG] Created new set {case_set.id} with {cases_created} cases")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ExcelImportResponse(
        case_set=CaseSetResponse(
            id=case_set.id,
            name=case_set.name,
            created_at=case_set.created_at,
            case_count=cases_created,
        ),
        cases_created=cases_created,
    )


# Test Case endpoints
@router.get("/sets/{case_set_id}/cases", response_model=list[TestCaseResponse])
async def get_test_cases(
    case_set_id: str,
    service: CaseService = Depends(get_case_service),
) -> list[TestCaseResponse]:
    """Get all test cases for a case set."""
    # Verify case set exists
    case_set = await service.get_case_set(case_set_id)
    if case_set is None:
        raise HTTPException(status_code=404, detail="用例集不存在")

    test_cases = await service.get_test_cases(case_set_id)
    return [
        TestCaseResponse(
            id=tc.id,
            set_id=tc.set_id,
            case_uid=tc.case_uid,
            description=tc.description,
            user_input=tc.user_input,
            expected_output=tc.expected_output,
            created_at=tc.created_at,
        )
        for tc in test_cases
    ]


@router.get("/cases/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> TestCaseResponse:
    """Get a test case by ID."""
    test_case = await service.get_test_case(case_id)
    if test_case is None:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return TestCaseResponse(
        id=test_case.id,
        set_id=test_case.set_id,
        case_uid=test_case.case_uid,
        description=test_case.description,
        user_input=test_case.user_input,
        expected_output=test_case.expected_output,
        created_at=test_case.created_at,
    )


@router.post("/cases", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    data: TestCaseCreate,
    service: CaseService = Depends(get_case_service),
) -> TestCaseResponse:
    """Create a new test case."""
    # Verify case set exists
    case_set = await service.get_case_set(data.set_id)
    if case_set is None:
        raise HTTPException(status_code=404, detail="用例集不存在")

    test_case = await service.create_test_case(data)
    return TestCaseResponse(
        id=test_case.id,
        set_id=test_case.set_id,
        case_uid=test_case.case_uid,
        description=test_case.description,
        user_input=test_case.user_input,
        expected_output=test_case.expected_output,
        created_at=test_case.created_at,
    )


@router.put("/cases/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    case_id: str,
    data: TestCaseUpdate,
    service: CaseService = Depends(get_case_service),
) -> TestCaseResponse:
    """Update a test case."""
    test_case = await service.update_test_case(case_id, data)
    if test_case is None:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return TestCaseResponse(
        id=test_case.id,
        set_id=test_case.set_id,
        case_uid=test_case.case_uid,
        description=test_case.description,
        user_input=test_case.user_input,
        expected_output=test_case.expected_output,
        created_at=test_case.created_at,
    )


@router.delete("/cases/{case_id}", status_code=204)
async def delete_test_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> None:
    """Delete a test case."""
    deleted = await service.delete_test_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="测试用例不存在")


@router.delete("/sets/{case_set_id}/cases", status_code=204)
async def delete_test_cases(
    case_set_id: str,
    service: CaseService = Depends(get_case_service),
) -> None:
    """Delete all test cases in a case set."""
    # Verify case set exists
    case_set = await service.get_case_set(case_set_id)
    if case_set is None:
        raise HTTPException(status_code=404, detail="用例集不存在")

    test_cases = await service.get_test_cases(case_set_id)
    for tc in test_cases:
        await service.delete_test_case(tc.id)
