"""API routes for evaluator management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.evaluator import (
    EvaluatorCreate,
    EvaluatorUpdate,
    EvaluatorResponse,
    TaskEvaluatorUpdate,
    EvaluatorTestRequest,
    EvaluatorTestResponse,
)
from app.services.evaluator_service import EvaluatorService
from app.models.evaluator import Evaluator

router = APIRouter(prefix="/api/evaluators", tags=["evaluators"])


@router.get("", response_model=List[EvaluatorResponse])
async def list_evaluators(
    type_filter: str = None,
    session: AsyncSession = Depends(get_db),
):
    """Get all evaluators.

    Args:
        type_filter: Optional filter by evaluator type
        session: Database session

    Returns:
        List of evaluators
    """
    service = await EvaluatorService.create(session)
    evaluators = await service.get_evaluators(type_filter=type_filter)
    return [
        EvaluatorResponse(
            id=e.id,
            name=e.name,
            description=e.description,
            type=e.type,
            config=e.config_dict,
            is_system=bool(e.is_system),
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in evaluators
    ]


@router.post("", response_model=EvaluatorResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluator(
    data: EvaluatorCreate,
    session: AsyncSession = Depends(get_db),
):
    """Create a new evaluator.

    Args:
        data: Evaluator creation data
        session: Database session

    Returns:
        Created evaluator

    Raises:
        HTTPException: If validation fails
    """
    service = await EvaluatorService.create(session)
    try:
        evaluator = await service.create_evaluator(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return EvaluatorResponse(
        id=evaluator.id,
        name=evaluator.name,
        description=evaluator.description,
        type=evaluator.type,
        config=evaluator.config_dict,
        is_system=bool(evaluator.is_system),
        created_at=evaluator.created_at,
        updated_at=evaluator.updated_at,
    )


@router.get("/{evaluator_id}", response_model=EvaluatorResponse)
async def get_evaluator(
    evaluator_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get an evaluator by ID.

    Args:
        evaluator_id: Evaluator ID
        session: Database session

    Returns:
        Evaluator details

    Raises:
        HTTPException: If evaluator not found
    """
    service = await EvaluatorService.create(session)
    evaluator = await service.get_evaluator(evaluator_id)
    if evaluator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"评估器不存在: {evaluator_id}",
        )

    return EvaluatorResponse(
        id=evaluator.id,
        name=evaluator.name,
        description=evaluator.description,
        type=evaluator.type,
        config=evaluator.config_dict,
        is_system=bool(evaluator.is_system),
        created_at=evaluator.created_at,
        updated_at=evaluator.updated_at,
    )


@router.put("/{evaluator_id}", response_model=EvaluatorResponse)
async def update_evaluator(
    evaluator_id: str,
    data: EvaluatorUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Update an evaluator.

    Args:
        evaluator_id: Evaluator ID
        data: Update data
        session: Database session

    Returns:
        Updated evaluator

    Raises:
        HTTPException: If evaluator not found or validation fails
    """
    service = await EvaluatorService.create(session)
    try:
        evaluator = await service.update_evaluator(evaluator_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return EvaluatorResponse(
        id=evaluator.id,
        name=evaluator.name,
        description=evaluator.description,
        type=evaluator.type,
        config=evaluator.config_dict,
        is_system=bool(evaluator.is_system),
        created_at=evaluator.created_at,
        updated_at=evaluator.updated_at,
    )


@router.delete("/{evaluator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluator(
    evaluator_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Delete an evaluator.

    Args:
        evaluator_id: Evaluator ID
        session: Database session

    Raises:
        HTTPException: If evaluator not found or is system evaluator
    """
    service = await EvaluatorService.create(session)
    try:
        deleted = await service.delete_evaluator(evaluator_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"评估器不存在: {evaluator_id}",
        )


@router.post("/{evaluator_id}/test", response_model=EvaluatorTestResponse)
async def test_evaluator(
    evaluator_id: str,
    data: EvaluatorTestRequest,
    session: AsyncSession = Depends(get_db),
):
    """Test an evaluator with sample data.

    Args:
        evaluator_id: Evaluator ID
        data: Test data with expected and actual values
        session: Database session

    Returns:
        Test result

    Raises:
        HTTPException: If evaluator not found
    """
    from app.evaluators.exact_match import ExactMatchEvaluator
    from app.evaluators.json_compare import JsonCompareEvaluator
    from app.evaluators.code_executor import CodeEvaluator
    from app.utils.llm_client import LlmClient
    from app.models.model_provider import ModelProvider
    from app.models.model import Model
    from sqlalchemy import select

    service = await EvaluatorService.create(session)
    evaluator = await service.get_evaluator(evaluator_id)
    if evaluator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"评估器不存在: {evaluator_id}",
        )

    try:
        config = evaluator.config_dict

        if evaluator.type == "code":
            # Check if it's a system evaluator with built-in implementation
            if evaluator.name == "exact_match":
                eval_instance = ExactMatchEvaluator()
                is_passed, reason = eval_instance.evaluate(data.expected, data.actual)
                return EvaluatorTestResponse(
                    result="passed" if is_passed else "failed",
                    reason=reason,
                )
            elif evaluator.name == "json_compare":
                eval_instance = JsonCompareEvaluator()
                is_passed, reason = eval_instance.evaluate(data.expected, data.actual)
                return EvaluatorTestResponse(
                    result="passed" if is_passed else "failed",
                    reason=reason,
                )
            else:
                # Custom code evaluator
                code = config.get("code", "")
                eval_instance = CodeEvaluator(code)
                is_passed, reason = await eval_instance.evaluate_async(
                    data.expected, data.actual
                )
                return EvaluatorTestResponse(
                    result="passed" if is_passed else "failed",
                    reason=reason,
                )

        elif evaluator.type == "llm_judge":
            # Get model_id from config
            model_id = config.get("model_id")
            if not model_id:
                return EvaluatorTestResponse(
                    result="failed",
                    error="LLM评估器未配置模型，请在评估器配置中选择模型",
                )

            # Get the configured model
            result = await session.execute(
                select(Model, ModelProvider)
                .join(ModelProvider, Model.provider_id == ModelProvider.id)
                .where(Model.id == model_id)
            )
            row = result.first()
            if row is None:
                return EvaluatorTestResponse(
                    result="failed",
                    error=f"配置的模型不存在 (model_id: {model_id})",
                )

            model, provider = row
            print(f"[DEBUG] Model: {model.model_code}, Provider: {provider.base_url}")

            llm_client = LlmClient(
                base_url=provider.base_url,
                api_key=provider.api_key,
            )

            prompt_template = config.get("prompt_template", "")
            # Use replace instead of format to avoid issues with JSON examples in template
            prompt = prompt_template.replace("${expected}", data.expected).replace("${actual}", data.actual)

            # Make async LLM call
            request = {
                "model": model.model_code,
                "messages": [
                    {"role": "system", "content": "你是一个专业的评估助手。请以JSON格式返回评估结果。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }

            try:
                print(f"[DEBUG] Calling LLM with model: {model.model_code}")
                response = await llm_client.call_llm(request)
                print(f"[DEBUG] LLM response type: {type(response)}")
                print(f"[DEBUG] LLM response (first 500 chars): {repr(response[:500] if response else 'None')}")

                if response is None:
                    return EvaluatorTestResponse(
                        result="failed",
                        error="LLM调用失败: 未获得响应，请检查模型配置和API地址",
                    )

                # Check if response contains error markers
                if isinstance(response, str) and ("[PARSE_ERROR]" in response or "[JSON_PARSE_ERROR]" in response):
                    return EvaluatorTestResponse(
                        result="failed",
                        error=f"LLM响应解析失败: {response}",
                    )

                # Parse JSON response with repair fallback
                import json
                try:
                    result_data = json.loads(response)
                    print(f"[DEBUG] Parsed result_data: {result_data}")

                    result_value = result_data.get("result", "failed")
                    if isinstance(result_value, str):
                        result_value = result_value.lower()
                    else:
                        result_value = "failed"

                    reason = result_data.get("reason", "")
                    if not isinstance(reason, str):
                        reason = str(reason) if reason else ""

                    return EvaluatorTestResponse(
                        result="passed" if result_value == "passed" else "failed",
                        reason=reason,
                    )
                except json.JSONDecodeError as je:
                    print(f"[DEBUG] JSON decode error: {je}")
                    # Try to repair JSON
                    try:
                        from app.utils.json_repair import JsonRepair
                        repaired = JsonRepair.repair(response)
                        print(f"[DEBUG] Repaired JSON: {repr(repaired[:500] if repaired else 'None')}")
                        result_data = json.loads(repaired)

                        result_value = result_data.get("result", "failed")
                        if isinstance(result_value, str):
                            result_value = result_value.lower()
                        else:
                            result_value = "failed"

                        reason = result_data.get("reason", "")
                        if not isinstance(reason, str):
                            reason = str(reason) if reason else ""

                        return EvaluatorTestResponse(
                            result="passed" if result_value == "passed" else "failed",
                            reason=reason,
                        )
                    except Exception as repair_err:
                        return EvaluatorTestResponse(
                            result="failed",
                            error=f"LLM返回无效JSON，修复失败: {str(repair_err)}. 原始响应: {response[:200]}",
                        )
                except Exception as parse_err:
                    return EvaluatorTestResponse(
                        result="failed",
                        error=f"解析LLM响应时出错: {type(parse_err).__name__}: {str(parse_err)}. 响应: {response[:200]}",
                    )
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[DEBUG] LLM call exception: {type(e).__name__}: {e}")
                print(f"[DEBUG] Traceback: {error_trace}")
                return EvaluatorTestResponse(
                    result="failed",
                    error=f"LLM调用失败: {type(e).__name__}: {str(e)}",
                )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DEBUG] Test evaluator exception: {type(e).__name__}: {e}")
        print(f"[DEBUG] Traceback: {error_trace}")
        return EvaluatorTestResponse(
            result="failed",
            error=f"{type(e).__name__}: {str(e)}",
        )


@router.get("/tasks/{task_id}/evaluators")
async def get_task_evaluators(
    task_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get evaluators configured for a task.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        List of task evaluators
    """
    service = await EvaluatorService.create(session)
    evaluators = await service.get_task_evaluators(task_id)
    return {"evaluators": evaluators}


@router.get("/debug/evaluators/{evaluator_id}")
async def debug_evaluator(
    evaluator_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Debug endpoint to get full evaluator details."""
    from sqlalchemy import select

    result = await session.execute(
        select(Evaluator).where(Evaluator.id == evaluator_id)
    )
    evaluator = result.scalar_one_or_none()
    if evaluator is None:
        return {"error": "Evaluator not found"}

    return {
        "id": evaluator.id,
        "name": evaluator.name,
        "type": evaluator.type,
        "config": evaluator.config_dict,
        "config_raw": evaluator.config,
    }


@router.put("/tasks/{task_id}/evaluators", status_code=status.HTTP_204_NO_CONTENT)
async def set_task_evaluators(
    task_id: str,
    data: TaskEvaluatorUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Set evaluators for a task.

    Args:
        task_id: Task ID
        data: List of evaluator IDs in order
        session: Database session

    Raises:
        HTTPException: If task or evaluator not found
    """
    service = await EvaluatorService.create(session)
    try:
        await service.set_task_evaluators(task_id, data.evaluator_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
