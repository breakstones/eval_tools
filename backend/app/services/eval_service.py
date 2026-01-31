"""Service for evaluation task management."""

import asyncio
import json
from typing import Any, Optional, List, Tuple, Dict, Callable
from collections.abc import AsyncIterator
from datetime import datetime
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_set import CaseSet
from app.models.eval_result import EvalResult
from app.models.eval_run import EvalRun
from app.models.eval_task import EvalTask
from app.models.test_case import TestCase
from app.models.model import Model
from app.models.model_provider import ModelProvider
from app.schemas.eval import EvalSummary, EvalTaskCreate, RequestTemplate
from app.evaluators.base import BaseEvaluator
from app.evaluators.exact_match import ExactMatchEvaluator
from app.evaluators.json_compare import JsonCompareEvaluator
from app.utils.llm_client import LlmClient
from app.utils.templater import TemplateRenderer
from app.database import async_session_factory


class EvalService:
    """Service for managing evaluation tasks."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Database session
        """
        self.session = session
        self.evaluators: Dict[str, type[BaseEvaluator]] = {
            "exact_match": ExactMatchEvaluator,
            "json_compare": JsonCompareEvaluator,
        }

    @classmethod
    async def create(cls, session: AsyncSession) -> Self:
        """Create a new service instance.

        Args:
            session: Database session

        Returns:
            EvalService instance
        """
        return cls(session)

    def _get_evaluator(self, evaluator_type: str) -> BaseEvaluator:
        """Get an evaluator instance by type.

        Args:
            evaluator_type: Type of evaluator

        Returns:
            Evaluator instance

        Raises:
            ValueError: If evaluator type is not found
        """
        evaluator_class = self.evaluators.get(evaluator_type)
        if evaluator_class is None:
            raise ValueError(f"未知的评估器类型: {evaluator_type}")
        return evaluator_class()

    async def get_eval_tasks(self, set_id: Optional[str] = None) -> List[EvalTask]:
        """Get evaluation tasks.

        Args:
            set_id: Optional case set ID to filter by

        Returns:
            List of evaluation tasks
        """
        query = select(EvalTask).order_by(EvalTask.created_at.desc())
        if set_id:
            query = query.where(EvalTask.set_id == set_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_eval_task(self, task_id: str) -> Optional[EvalTask]:
        """Get an evaluation task by ID.

        Args:
            task_id: Task ID

        Returns:
            Evaluation task or None if not found
        """
        result = await self.session.execute(
            select(EvalTask).where(EvalTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def create_eval_task(self, data: EvalTaskCreate) -> EvalTask:
        """Create a new evaluation task.

        Args:
            data: Task creation data

        Returns:
            Created task
        """
        # Verify case set exists
        case_set_result = await self.session.execute(
            select(CaseSet).where(CaseSet.id == data.set_id)
        )
        case_set = case_set_result.scalar_one_or_none()
        if case_set is None:
            raise ValueError(f"用例集不存在: {data.set_id}")

        # Verify model exists
        model_result = await self.session.execute(
            select(Model, ModelProvider).where(Model.id == data.model_id)
        )
        model_row = model_result.first()
        if model_row is None:
            raise ValueError(f"模型不存在: {data.model_id}")

        # Get default request template if not provided
        if data.request_template is None:
            request_template = {
                "model": "${model_name}",
                "messages": [
                    {"role": "system", "content": "${system_prompt}"},
                    {"role": "user", "content": "${case.user_input}"},
                ],
            }
        else:
            request_template = data.request_template.model_dump()

        # Create task
        task = EvalTask(
            set_id=data.set_id,
            model_id=data.model_id,
            request_template=json.dumps(request_template),
            system_prompt=data.system_prompt,
            status="PENDING",
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update_eval_task(
        self,
        task_id: str,
        model_id: Optional[str] = None,
        request_template: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        concurrency: Optional[int] = None
    ) -> EvalTask:
        """Update an evaluation task.

        Args:
            task_id: Task ID
            model_id: New model ID
            request_template: New request template
            system_prompt: New system prompt
            concurrency: Concurrent execution count

        Returns:
            Updated task

        Raises:
            ValueError: If task not found
        """
        task = await self.get_eval_task(task_id)
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")

        if model_id is not None:
            # Verify model exists
            model_result = await self.session.execute(
                select(Model, ModelProvider).where(Model.id == model_id)
            )
            model_row = model_result.first()
            if model_row is None:
                raise ValueError(f"模型不存在: {model_id}")
            task.model_id = model_id

        if concurrency is not None:
            # Validate concurrency value
            if concurrency < 1:
                raise ValueError("并发数量必须大于等于1")
            if concurrency > 100:
                raise ValueError("并发数量不能超过100")
            task.concurrency = concurrency

        if request_template is not None:
            task.request_template_dict = request_template

        if system_prompt is not None:
            task.system_prompt = system_prompt

        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete_eval_task(self, task_id: str) -> bool:
        """Delete an evaluation task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = await self.get_eval_task(task_id)
        if task is None:
            return False

        # Delete results (cascade will delete runs)
        await self.session.execute(delete(EvalResult).where(EvalResult.task_id == task_id))

        # Delete runs
        await self.session.execute(delete(EvalRun).where(EvalRun.task_id == task_id))

        # Delete task
        await self.session.execute(delete(EvalTask).where(EvalTask.id == task_id))
        return True

    async def get_eval_results(self, task_id: str) -> List[Tuple[EvalResult, TestCase]]:
        """Get evaluation results for a task with associated test cases.

        Args:
            task_id: Task ID

        Returns:
            List of (result, test_case) tuples
        """
        result = await self.session.execute(
            select(EvalResult, TestCase)
            .join(TestCase, EvalResult.case_id == TestCase.id)
            .where(EvalResult.task_id == task_id)
            .order_by(TestCase.created_at.asc())
        )
        return list(result.all())

    async def get_eval_result(self, result_id: str) -> Optional[Tuple[EvalResult, TestCase]]:
        """Get a single evaluation result with test case.

        Args:
            result_id: Result ID

        Returns:
            Tuple of (result, test_case) or None if not found
        """
        result = await self.session.execute(
            select(EvalResult, TestCase)
            .join(TestCase, EvalResult.case_id == TestCase.id)
            .where(EvalResult.id == result_id)
        )
        return result.first()

    async def get_eval_runs(self, task_id: str) -> List[EvalRun]:
        """Get all runs for an evaluation task.

        Args:
            task_id: Task ID

        Returns:
            List of evaluation runs
        """
        result = await self.session.execute(
            select(EvalRun).where(EvalRun.task_id == task_id)
            .order_by(EvalRun.run_number.desc())
        )
        return list(result.scalars().all())

    async def get_eval_run(self, run_id: str) -> Optional[EvalRun]:
        """Get an evaluation run by ID.

        Args:
            run_id: Run ID

        Returns:
            Evaluation run or None if not found
        """
        result = await self.session.execute(
            select(EvalRun).where(EvalRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_run_results(self, run_id: str) -> List[Tuple[EvalResult, TestCase]]:
        """Get evaluation results for a specific run with associated test cases.

        Args:
            run_id: Run ID

        Returns:
            List of (result, test_case) tuples
        """
        result = await self.session.execute(
            select(EvalResult, TestCase)
            .join(TestCase, EvalResult.case_id == TestCase.id)
            .where(EvalResult.run_id == run_id)
            .order_by(TestCase.created_at.asc())
        )
        return list(result.all())

    async def create_eval_run(self, task_id: str) -> EvalRun:
        """Create a new evaluation run for a task.

        Args:
            task_id: Task ID

        Returns:
            Created run
        """
        # Get existing runs to determine next run number
        existing_result = await self.session.execute(
            select(func.count(EvalRun.id)).where(EvalRun.task_id == task_id)
        )
        run_count = existing_result.scalar() or 0
        next_run_number = run_count + 1

        # Create run
        run = EvalRun(
            task_id=task_id,
            run_number=next_run_number,
            status="PENDING",
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_run_number(self, run_id: str) -> int:
        """Get the run number for a run ID.

        Args:
            run_id: Run ID

        Returns:
            Run number
        """
        result = await self.session.execute(
            select(EvalRun.run_number).where(EvalRun.id == run_id)
        )
        run_number = result.scalar_one_or_none()
        return run_number if run_number is not None else 0

    async def run_evaluation_with_ws(
        self,
        run_id: str,
        task_id: str,
        ws_manager,
    ) -> Dict[str, Any]:
        """Run evaluation and broadcast updates via WebSocket with concurrent execution.

        Args:
            run_id: Run ID
            task_id: Task ID
            ws_manager: WebSocket connection manager

        Returns:
            Summary dictionary
        """
        print(f"[DEBUG] run_evaluation_with_ws started: run_id={run_id}, task_id={task_id}")
        from app.models.case_set import CaseSet

        # Get run with task
        run_result = await self.session.execute(
            select(EvalRun).where(EvalRun.id == run_id)
        )
        run = run_result.scalar_one_or_none()
        if run is None:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}

        # Get task with related data
        task_result = await self.session.execute(
            select(EvalTask, CaseSet, Model, ModelProvider)
            .join(CaseSet, EvalTask.set_id == CaseSet.id)
            .join(Model, EvalTask.model_id == Model.id)
            .join(ModelProvider, Model.provider_id == ModelProvider.id)
            .where(EvalTask.id == task_id)
        )
        row = task_result.first()
        if row is None:
            run.status = "FAILED"
            run.error = "任务不存在"
            await self.session.commit()
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}

        task, case_set, model, provider = row

        # Get all test cases
        cases_result = await self.session.execute(
            select(TestCase).where(TestCase.set_id == case_set.id)
        )
        cases = list(cases_result.scalars().all())

        if not cases:
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            summary = {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}
            run.summary = json.dumps(summary)
            await self.session.commit()
            return summary

        # Initialize counters
        total = len(cases)
        passed = 0
        failed = 0

        # Get concurrency from task (default to 1 if not set)
        concurrency = getattr(task, 'concurrency', 1) or 1
        # Ensure concurrency is at least 1 and at most total
        concurrency = max(1, min(concurrency, total))
        print(f"[DEBUG] Evaluation setup: total={total}, concurrency={concurrency}")

        # Create semaphore to control concurrency
        semaphore = asyncio.Semaphore(concurrency)
        print(f"[DEBUG] Semaphore created with concurrency={concurrency}")

        # Create LLM client and template renderer
        llm_client = LlmClient(
            base_url=provider.base_url,
            api_key=provider.api_key,
        )
        renderer = TemplateRenderer()

        # Queue to maintain result order
        result_queue: asyncio.Queue[Tuple[int, Dict]] = asyncio.Queue()

        async def evaluate_single_case(index: int, case: TestCase) -> None:
            """Evaluate a single test case and put result in queue."""
            async with semaphore:
                # Prepare context
                context = {
                    "model_name": model.model_code,
                    "system_prompt": task.system_prompt or "",
                    "task_config": {
                        "base_url": provider.base_url,
                        "api_key": provider.api_key,
                        "model_code": model.model_code,
                    },
                    "case_set": {"name": case_set.name or ""},
                    "case": {
                        "user_input": case.user_input,
                        "case_uid": case.case_uid,
                        "description": case.description,
                    },
                }

                # Render request template
                rendered_request = renderer.render_request_template(
                    task.request_template_dict,
                    context,
                )

                # Call LLM
                actual_output = None
                execution_error = None
                try:
                    response = await llm_client.call_llm(rendered_request)
                    actual_output = response
                except Exception as e:
                    execution_error = str(e)

                # Evaluate result
                evaluator_logs = []
                is_passed = False

                if actual_output is not None:
                    evaluator = ExactMatchEvaluator()
                    is_passed, evaluator_log = evaluator.evaluate(
                        case.expected_output or "",
                        actual_output,
                    )
                    evaluator_logs.append(evaluator_log)
                else:
                    # Execution failed
                    is_passed = False

                # Put result in queue
                await result_queue.put((index, {
                    "case": case,
                    "actual_output": actual_output,
                    "is_passed": is_passed,
                    "execution_error": execution_error,
                    "evaluator_logs": evaluator_logs,
                }))

        # Create all evaluation tasks
        tasks = [
            evaluate_single_case(index, case)
            for index, case in enumerate(cases, start=1)
        ]

        # Create a consumer coroutine to process results in order
        async def result_consumer():
            nonlocal passed, failed
            completed = 0
            next_expected_index = 1  # Start from 1 since enumerate starts at 1
            results_buffer: Dict[int, Dict] = {}

            while completed < total:
                # Wait for any result
                index, result_data = await result_queue.get()
                results_buffer[index] = result_data
                completed += 1

                # Process results in order - process consecutive available indices
                while next_expected_index in results_buffer:
                    next_result = results_buffer.pop(next_expected_index)

                    case = next_result["case"]

                    # Create result record
                    result = EvalResult(
                        run_id=run_id,
                        task_id=task_id,
                        case_id=case.id,
                        actual_output=next_result["actual_output"],
                        is_passed=next_result["is_passed"],
                        execution_error=next_result["execution_error"],
                        evaluator_logs=json.dumps(next_result["evaluator_logs"]),
                    )
                    self.session.add(result)
                    await self.session.flush()

                    # Broadcast result via WebSocket
                    await ws_manager.broadcast_event(
                        task_id,
                        "result",
                        {
                            "index": next_expected_index,
                            "total": total,
                            "case_id": case.id,
                            "case_uid": case.case_uid,
                            "is_passed": next_result["is_passed"],
                            "actual_output": next_result["actual_output"],
                            "execution_error": next_result["execution_error"],
                        },
                    )

                    # Update counters
                    if next_result["is_passed"]:
                        passed += 1
                    else:
                        failed += 1

                    # Move to next expected index
                    next_expected_index += 1

        # Start all evaluation tasks and consumer task
        evaluation_tasks = [asyncio.create_task(task) for task in tasks]
        consumer_task = asyncio.create_task(result_consumer())

        # Wait for all evaluation tasks to complete
        await asyncio.gather(*evaluation_tasks)

        # Wait for consumer to finish processing all results
        await consumer_task

        # Update run status
        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        }
        run.summary = json.dumps(summary)

        # Update task summary
        task.summary_dict = summary

        await self.session.commit()
        return summary

    async def get_model_with_provider(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a model with its provider details.

        Args:
            model_id: Model ID

        Returns:
            Dictionary with model and provider details
        """
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
            },
        }

    async def test_template(
        self,
        task_id: str,
        case_id: Optional[str] = None,
        test_input: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """Test request template rendering and optionally send a real request.

        Args:
            task_id: Task ID
            case_id: Optional test case ID to use for rendering
            test_input: Optional test input to use instead of a case

        Returns:
            Tuple of (rendered_request, actual_response, error)
        """
        # Get task with model and provider
        task_result = await self.session.execute(
            select(EvalTask, CaseSet, Model, ModelProvider)
            .join(CaseSet, EvalTask.set_id == CaseSet.id)
            .join(Model, EvalTask.model_id == Model.id)
            .join(ModelProvider, Model.provider_id == ModelProvider.id)
            .where(EvalTask.id == task_id)
        )
        row = task_result.first()
        if row is None:
            raise ValueError(f"任务不存在: {task_id}")

        task, case_set, model, provider = row

        # Get test case if provided
        test_case = None
        if case_id:
            case_result = await self.session.execute(
                select(TestCase).where(TestCase.id == case_id)
            )
            test_case = case_result.scalar_one_or_none()

        # Prepare context for template rendering
        request_template = task.request_template_dict or {}
        # Use system_prompt from task
        system_prompt = task.system_prompt or ""

        # Debug: print context
        print(f"[DEBUG] test_template context:")
        print(f"[DEBUG]   task.system_prompt = {repr(task.system_prompt[:50] if task.system_prompt else None)}...")
        print(f"[DEBUG]   resolved system_prompt = {repr(system_prompt[:50] if system_prompt else 'EMPTY')}...")

        context = {
            "model_name": model.model_code,
            "system_prompt": system_prompt,
            "task_config": {
                "base_url": provider.base_url,
                "api_key": provider.api_key,
                "model_code": model.model_code,
            },
            "case_set": {
                "name": case_set.name or "",
            },
            "case": {
                "user_input": test_input or (test_case.user_input if test_case else ""),
                "case_uid": test_case.case_uid if test_case else "",
                "description": test_case.description if test_case else "",
            },
        }

        # Render template
        renderer = TemplateRenderer()
        rendered_request = renderer.render_request_template(
            task.request_template_dict,
            context,
        )

        # Debug: print rendered result
        print(f"[DEBUG] Rendered request:")
        print(f"[DEBUG]   system_prompt in messages: {rendered_request.get('messages', [{}])[0].get('content', 'NO_CONTENT')[:100] if rendered_request.get('messages') else 'NO_MESSAGES'}...")
        print(f"[DEBUG]   Full rendered: {json.dumps(rendered_request, ensure_ascii=False)[:200]}...")

        # Try to send actual request
        actual_response = None
        error = None
        try:
            llm_client = LlmClient(
                base_url=provider.base_url,
                api_key=provider.api_key,
            )
            actual_response = await llm_client.call_llm(rendered_request)
        except Exception as e:
            error = str(e)

        return rendered_request, actual_response, error

    async def _run_evaluation(
        self,
        run_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """Run a single evaluation.

        Args:
            run_id: Run ID
            progress_callback: Optional callback for progress updates
        """
        from app.models.case_set import CaseSet

        # Get run with task
        run_result = await self.session.execute(
            select(EvalRun).where(EvalRun.id == run_id)
        )
        run = run_result.scalar_one_or_none()
        if run is None:
            return

        task_id = run.task_id

        # Get task with related data
        task_result = await self.session.execute(
            select(EvalTask, CaseSet, Model, ModelProvider)
            .join(CaseSet, EvalTask.set_id == CaseSet.id)
            .join(Model, EvalTask.model_id == Model.id)
            .join(ModelProvider, Model.provider_id == ModelProvider.id)
            .where(EvalTask.id == task_id)
        )
        row = task_result.first()
        if row is None:
            run.status = "FAILED"
            run.error = "任务不存在"
            await self.session.commit()
            return

        task, case_set, model, provider = row

        # Get all test cases for the case set
        cases_result = await self.session.execute(
            select(TestCase).where(TestCase.set_id == case_set.id)
        )
        cases = list(cases_result.scalars().all())

        if not cases:
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = json.dumps({"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0})
            await self.session.commit()
            return

        # Initialize counters
        total = len(cases)
        passed = 0
        failed = 0

        # Create LLM client
        llm_client = LlmClient(
            base_url=provider.base_url,
            api_key=provider.api_key,
        )

        # Create template renderer
        renderer = TemplateRenderer()

        # Evaluate each case
        for index, case in enumerate(cases, start=1):
            # Prepare context
            request_template = task.request_template_dict or {}
            # Use system_prompt from task
            system_prompt = task.system_prompt or ""

            context = {
                "model_name": model.model_code,
                "system_prompt": system_prompt,
                "task_config": {
                    "base_url": provider.base_url,
                    "api_key": provider.api_key,
                    "model_code": model.model_code,
                },
                "case_set": {
                    "name": case_set.name or "",
                },
                "case": {
                    "user_input": case.user_input,
                    "case_uid": case.case_uid,
                    "description": case.description,
                },
            }

            # Render request template
            rendered_request = renderer.render_request_template(
                task.request_template_dict,
                context,
            )

            # Call LLM
            actual_output = None
            execution_error = None
            try:
                actual_output = await llm_client.call_llm(rendered_request)
            except Exception as e:
                execution_error = str(e)

            # Evaluate result
            evaluator_logs = []
            is_passed = False

            if actual_output is not None:
                # Try exact match evaluator by default
                evaluator = ExactMatchEvaluator()
                is_passed, evaluator_log = evaluator.evaluate(
                    case.expected_output or "",
                    actual_output,
                )
                evaluator_logs.append(evaluator_log)
            else:
                # Execution failed - count as failed
                failed += 1

            # Create result
            result = EvalResult(
                run_id=run.id,
                task_id=task_id,
                case_id=case.id,
                actual_output=actual_output,
                is_passed=is_passed,
                execution_error=execution_error,
                evaluator_logs=json.dumps(evaluator_logs),
            )
            self.session.add(result)
            await self.session.flush()

            # Call progress callback if provided
            if progress_callback:
                await progress_callback({
                    "run_id": run.id,
                    "task_id": task_id,
                    "index": index,
                    "total": total,
                    "case_id": case.id,
                    "case_uid": case.case_uid,
                    "result_id": result.id,
                    "actual_output": actual_output,
                    "is_passed": is_passed,
                    "evaluator_logs": evaluator_logs,
                })

            if is_passed:
                passed += 1
            else:
                failed += 1

        # Update run status
        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        run.summary = json.dumps({
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        })

        # Update task summary
        task.summary_dict = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        }

        await self.session.commit()

    async def stream_evaluation(self, task_id: str) -> AsyncIterator[str]:
        """Stream evaluation progress via Server-Sent Events.

        Args:
            task_id: Task ID

        Yields:
            SSE event strings
        """
        # Check if there's already a running or recently created run for this task
        from sqlalchemy import select, and_
        from datetime import datetime, timedelta

        # Check for running runs first
        result = await self.session.execute(
            select(EvalRun)
            .where(
                and_(
                    EvalRun.task_id == task_id,
                    EvalRun.status.in_(["PENDING", "RUNNING"])
                )
            )
            .order_by(EvalRun.started_at.desc())
            .limit(1)
        )
        existing_run = result.scalar_one_or_none()

        if existing_run:
            # Use existing running run
            run = existing_run
        else:
            # Check for any run created within last 5 minutes to prevent duplicates
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            result = await self.session.execute(
                select(EvalRun)
                .where(
                    and_(
                        EvalRun.task_id == task_id,
                        EvalRun.started_at >= five_minutes_ago
                    )
                )
                .order_by(EvalRun.started_at.desc())
                .limit(1)
            )
            recent_run = result.scalar_one_or_none()

            if recent_run:
                # Use the recent run
                run = recent_run
                if run.status == "COMPLETED":
                    # Already completed - send completion without re-running
                    summary = json.loads(run.summary) if run.summary else {}
                    yield f"data: {json.dumps({'type': 'run_created', 'run_id': run.id, 'run_number': run.run_number})}\n\n"
                    yield f"data: {json.dumps({'type': 'complete', 'status': 'completed', 'summary': summary})}\n\n"
                    return
                # If PENDING or RUNNING, continue with it
            else:
                # Create a new run
                run = await self.create_eval_run(task_id)

        # Update task status
        task = await self.get_eval_task(task_id)
        if task is None:
            yield f"data: {json.dumps({'type': 'error', 'message': '任务不存在'})}\n\n"
            return

        task.status = "RUNNING"
        await self.session.commit()

        # Send run created event (or existing run info)
        yield f"data: {json.dumps({'type': 'run_created', 'run_id': run.id, 'run_number': run.run_number})}\n\n"

        # Store run_id to avoid accessing run object during evaluation
        run_id = run.id

        # Run evaluation directly in the same coroutine
        try:
            await self._run_evaluation(run_id, None)
        except Exception as e:
            # Update run status on error
            await self.session.refresh(run)
            run.status = "FAILED"
            run.error = str(e)
            await self.session.commit()
            yield f"data: {json.dumps({'type': 'error', 'status': 'failed', 'error': str(e)})}\n\n"

            # Update task status
            task = await self.get_eval_task(task_id)
            if task:
                task.status = "FAILED"
                await self.session.commit()
            return

        # Refresh run to get final status
        await self.session.refresh(run)

        # Get final summary
        summary = json.loads(run.summary) if run.summary else {}
        yield f"data: {json.dumps({'type': 'complete', 'status': 'completed', 'summary': summary})}\n\n"

        # Update task status
        task = await self.get_eval_task(task_id)
        if task:
            task.status = "COMPLETED"
            await self.session.commit()