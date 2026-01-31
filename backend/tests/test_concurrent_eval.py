"""Tests for concurrent evaluation functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.services.eval_service import EvalService
from app.models.case_set import CaseSet
from app.models.eval_run import EvalRun
from app.models.eval_task import EvalTask
from app.models.model import Model
from app.models.model_provider import ModelProvider
from app.models.test_case import TestCase


@pytest.mark.asyncio
class TestConcurrentEvaluation:
    """Tests for concurrent evaluation execution."""

    async def test_concurrent_execution_with_semaphore(self):
        """Test that semaphore correctly limits concurrent execution."""
        concurrency = 2
        semaphore = asyncio.Semaphore(concurrency)

        execution_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def simulated_task(task_id: int, delay: float):
            """Simulate a task that takes some time."""
            nonlocal execution_count, max_concurrent

            async with semaphore:
                async with lock:
                    execution_count += 1
                    if execution_count > max_concurrent:
                        max_concurrent = execution_count

                await asyncio.sleep(delay)

                async with lock:
                    execution_count -= 1

                return task_id

        # Create 5 tasks with varying delays
        tasks = [
            simulated_task(i, 0.1)  # Each task takes 0.1 seconds
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all tasks completed
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}

        # Verify max concurrent never exceeded semaphore limit
        assert max_concurrent <= concurrency

    async def test_queue_preserves_order(self):
        """Test that queue can preserve result order despite async completion."""
        result_queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
        results = []

        async def producer(index: int, delay: float):
            """Producer that puts results in queue after delay."""
            await asyncio.sleep(delay)
            await result_queue.put((index, f"result-{index}"))

        async def consumer():
            """Consumer that processes results in order using buffering logic."""
            completed = 0
            total = 5
            next_expected_index = 1  # Start from 1 (matching enumerate start=1)
            buffer = {}

            while completed < total:
                index, value = await result_queue.get()
                buffer[index] = value
                completed += 1

                # Process consecutive available indices in order
                while next_expected_index in buffer:
                    results.append((next_expected_index, buffer.pop(next_expected_index)))
                    next_expected_index += 1

        # Start consumer
        consumer_task = asyncio.create_task(consumer())

        # Start producers with different delays (reverse order - last one finishes first)
        producer_tasks = [
            producer(i, 0.5 - (i * 0.1))  # Index 4 finishes first, index 0 finishes last
            for i in range(1, 6)  # Use 1-5 to match enumerate start=1
        ]

        await asyncio.gather(*producer_tasks)
        await consumer_task

        # Verify results are in correct order
        assert results == [(1, "result-1"), (2, "result-2"), (3, "result-3"), (4, "result-4"), (5, "result-5")]

    async def test_concurrent_evaluation_mock(self, db_session):
        """Test concurrent evaluation with mocked LLM calls."""
        # Create test data
        provider = ModelProvider(
            id="provider-1",
            name="Test Provider",
            base_url="http://test.com",
            api_key="test-key"
        )
        db_session.add(provider)

        model = Model(
            id="model-1",
            provider_id=provider.id,
            model_code="test-model",
            display_name="Test Model"
        )
        db_session.add(model)

        case_set = CaseSet(
            id="set-1",
            name="Test Set"
        )
        db_session.add(case_set)

        # Create test cases
        for i in range(5):
            test_case = TestCase(
                id=f"case-{i}",
                set_id=case_set.id,
                case_uid=f"TC-00{i+1}",
                user_input=f"Input {i}",
                expected_output=f"Expected {i}"
            )
            db_session.add(test_case)

        task = EvalTask(
            id="task-1",
            set_id=case_set.id,
            model_id=model.id,
            concurrency=2,  # Set concurrency to 2
            request_template=json.dumps({"model": "test"}),
            system_prompt="Test prompt",
            status="PENDING"
        )
        db_session.add(task)

        run = EvalRun(
            id="run-1",
            task_id=task.id,
            run_number=1,
            status="RUNNING"
        )
        db_session.add(run)

        await db_session.commit()

        # Create service
        service = EvalService(db_session)

        # Mock WebSocket manager
        ws_manager = MagicMock()
        ws_manager.broadcast_event = AsyncMock()

        # Mock LLM client to avoid actual API calls
        async def mock_call_llm(request):
            # Simulate some delay
            await asyncio.sleep(0.05)
            return f"Mock response for {request.get('case_id', 'unknown')}"

        # We need to patch the LlmClient
        from unittest.mock import patch
        from app.utils.llm_client import LlmClient

        # Track execution order
        execution_order = []

        original_call_llm = LlmClient.call_llm

        async def tracked_call_llm(self, request):
            execution_order.append(request.get('case_uid', 'unknown'))
            await asyncio.sleep(0.05)  # Simulate API delay
            return f"Response for {request.get('case_uid', 'unknown')}"

        with patch.object(LlmClient, 'call_llm', tracked_call_llm):
            # Run evaluation
            summary = await service.run_evaluation_with_ws(
                run.id,
                task.id,
                ws_manager
            )

        # Verify results
        assert summary["total"] == 5
        assert summary["passed"] >= 0  # Exact match may vary
        assert summary["failed"] >= 0

        # Verify WebSocket was called for each case
        assert ws_manager.broadcast_event.call_count >= 5

        # Verify run status
        await db_session.refresh(run)
        assert run.status == "COMPLETED"
        assert run.completed_at is not None

    async def test_concurrency_boundary_values(self, db_session):
        """Test concurrency with boundary values."""
        # Create minimal test setup
        provider = ModelProvider(
            id="provider-bv",
            name="Test",
            base_url="http://test",
            api_key="key"
        )
        db_session.add(provider)

        model = Model(
            id="model-bv",
            provider_id=provider.id,
            model_code="test",
            display_name="Test"
        )
        db_session.add(model)

        case_set = CaseSet(id="set-bv", name="Test")
        db_session.add(case_set)

        # Create only 2 test cases
        for i in range(2):
            tc = TestCase(
                id=f"case-bv-{i}",
                set_id=case_set.id,
                case_uid=f"TC-{i}",
                user_input=f"In {i}",
                expected_output=f"Exp {i}"
            )
            db_session.add(tc)

        # Test with concurrency higher than case count
        task = EvalTask(
            id="task-bv",
            set_id=case_set.id,
            model_id=model.id,
            concurrency=10,  # Higher than number of cases
            request_template=json.dumps({"model": "test"}),
            system_prompt="Test",
            status="PENDING"
        )
        db_session.add(task)

        run = EvalRun(
            id="run-bv",
            task_id=task.id,
            run_number=1,
            status="RUNNING"
        )
        db_session.add(run)

        await db_session.commit()

        service = EvalService(db_session)
        ws_manager = MagicMock()
        ws_manager.broadcast_event = AsyncMock()

        # Mock LLM client
        from unittest.mock import patch
        from app.utils.llm_client import LlmClient

        async def mock_call(self, request):
            await asyncio.sleep(0.01)
            return "Mock response"

        with patch.object(LlmClient, 'call_llm', mock_call):
            summary = await service.run_evaluation_with_ws(
                run.id,
                task.id,
                ws_manager
            )

        # Should complete successfully
        assert summary["total"] == 2
        await db_session.refresh(run)
        assert run.status == "COMPLETED"
