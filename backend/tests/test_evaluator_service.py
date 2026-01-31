"""Tests for Evaluator Service."""

import json
import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evaluator_service import EvaluatorService
from app.schemas.evaluator import EvaluatorCreate, EvaluatorUpdate
from app.models.evaluator import Evaluator
from app.models.task_evaluator import TaskEvaluator
from sqlalchemy import delete


@pytest.fixture
async def evaluator_service(db_session: AsyncSession) -> EvaluatorService:
    """Create evaluator service fixture."""
    return await EvaluatorService.create(db_session)


@pytest.fixture
def sample_llm_judge_create():
    """Sample LLM judge creation data."""
    return EvaluatorCreate(
        name="test_llm_judge",
        description="测试LLM评估器",
        type="llm_judge",
        config={
            "prompt_template": "Evaluate: {expected} vs {actual}"
        }
    )


@pytest.fixture
def sample_code_evaluator_create():
    """Sample code evaluator creation data."""
    return EvaluatorCreate(
        name="test_code_evaluator",
        description="测试代码评估器",
        type="code",
        config={
            "code": "def evaluate(expected, actual): return {'result': 'passed', 'reason': 'test'}"
        }
    )


class TestEvaluatorService:
    """Tests for EvaluatorService class."""

    @pytest.mark.asyncio
    async def test_get_evaluators_empty(self, evaluator_service):
        """Test getting evaluators when none exist."""
        # Clear any existing evaluators
        from sqlalchemy import delete, text
        await evaluator_service.session.execute(
            delete(TaskEvaluator)
        )
        await evaluator_service.session.execute(
            delete(Evaluator)
        )
        await evaluator_service.session.commit()

        evaluators = await evaluator_service.get_evaluators()
        assert len(evaluators) == 0

    @pytest.mark.asyncio
    async def test_create_llm_judge_evaluator(
        self,
        evaluator_service,
        sample_llm_judge_create,
    ):
        """Test creating an LLM judge evaluator."""
        evaluator = await evaluator_service.create_evaluator(sample_llm_judge_create)

        assert evaluator.id is not None
        assert evaluator.name == "test_llm_judge"
        assert evaluator.type == "llm_judge"
        assert evaluator.is_system == 0
        assert "prompt_template" in evaluator.config_dict

    @pytest.mark.asyncio
    async def test_create_code_evaluator(
        self,
        evaluator_service,
        sample_code_evaluator_create,
    ):
        """Test creating a code evaluator."""
        evaluator = await evaluator_service.create_evaluator(sample_code_evaluator_create)

        assert evaluator.id is not None
        assert evaluator.name == "test_code_evaluator"
        assert evaluator.type == "code"
        assert evaluator.is_system == 0
        assert "code" in evaluator.config_dict

    @pytest.mark.asyncio
    async def test_create_evaluator_missing_prompt_template(self, evaluator_service):
        """Test creating LLM judge without prompt_template fails."""
        with pytest.raises(ValueError, match="prompt_template"):
            await evaluator_service.create_evaluator(
                EvaluatorCreate(
                    name="invalid_llm",
                    type="llm_judge",
                    config={}
                )
            )

    @pytest.mark.asyncio
    async def test_create_evaluator_missing_code(self, evaluator_service):
        """Test creating code evaluator without code fails."""
        with pytest.raises(ValueError, match="code"):
            await evaluator_service.create_evaluator(
                EvaluatorCreate(
                    name="invalid_code",
                    type="code",
                    config={}
                )
            )

    @pytest.mark.asyncio
    async def test_create_evaluator_duplicate_name(
        self,
        evaluator_service,
        sample_llm_judge_create,
    ):
        """Test creating evaluator with duplicate name fails."""
        await evaluator_service.create_evaluator(sample_llm_judge_create)

        with pytest.raises(ValueError, match="名称已存在"):
            await evaluator_service.create_evaluator(sample_llm_judge_create)

    @pytest.mark.asyncio
    async def test_get_evaluator_by_id(
        self,
        evaluator_service,
        sample_llm_judge_create,
    ):
        """Test getting evaluator by ID."""
        created = await evaluator_service.create_evaluator(sample_llm_judge_create)
        found = await evaluator_service.get_evaluator(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "test_llm_judge"

    @pytest.mark.asyncio
    async def test_get_evaluator_by_name(
        self,
        evaluator_service,
        sample_llm_judge_create,
    ):
        """Test getting evaluator by name."""
        await evaluator_service.create_evaluator(sample_llm_judge_create)
        found = await evaluator_service.get_evaluator_by_name("test_llm_judge")

        assert found is not None
        assert found.name == "test_llm_judge"

    @pytest.mark.asyncio
    async def test_update_evaluator(
        self,
        evaluator_service,
        sample_llm_judge_create,
    ):
        """Test updating an evaluator."""
        created = await evaluator_service.create_evaluator(sample_llm_judge_create)

        updated = await evaluator_service.update_evaluator(
            created.id,
            EvaluatorUpdate(
                description="Updated description",
                config={
                    "prompt_template": "New template: {expected} vs {actual}"
                }
            )
        )

        assert updated.description == "Updated description"
        assert "New template" in updated.config_dict["prompt_template"]

    @pytest.mark.asyncio
    async def test_update_system_evaluator_fails(
        self,
        evaluator_service,
        db_session: AsyncSession,
    ):
        """Test that updating system evaluator fails."""
        # Create a system evaluator for testing
        from app.models.evaluator import Evaluator
        system_eval = Evaluator(
            name="system_test_eval",
            description="System evaluator for testing",
            type="code",
            config='{"code": "def evaluate(e,a): return {\\\"result\\\": \\\"passed\\\", \\\"reason\\\": \\\"\\\"}"}',
            is_system=1,
        )
        db_session.add(system_eval)
        await db_session.flush()

        with pytest.raises(ValueError, match="不能修改系统内置评估器"):
            await evaluator_service.update_evaluator(
                system_eval.id,
                EvaluatorUpdate(description="New description")
            )

    @pytest.mark.asyncio
    async def test_delete_evaluator(
        self,
        evaluator_service,
        sample_code_evaluator_create,
    ):
        """Test deleting an evaluator."""
        created = await evaluator_service.create_evaluator(sample_code_evaluator_create)

        deleted = await evaluator_service.delete_evaluator(created.id)
        assert deleted is True

        found = await evaluator_service.get_evaluator(created.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_system_evaluator_fails(
        self,
        evaluator_service,
        db_session: AsyncSession,
    ):
        """Test that deleting system evaluator fails."""
        # Create a system evaluator for testing
        system_eval = Evaluator(
            name="system_test_eval2",
            description="System evaluator for testing",
            type="code",
            config='{"code": "def evaluate(e,a): return {\\\"result\\\": \\\"passed\\\"}"}',
            is_system=1,
        )
        db_session.add(system_eval)
        await db_session.flush()

        with pytest.raises(ValueError, match="不能删除系统内置评估器"):
            await evaluator_service.delete_evaluator(system_eval.id)

    @pytest.mark.asyncio
    async def test_get_evaluators_by_type(
        self,
        evaluator_service,
        sample_llm_judge_create,
        sample_code_evaluator_create,
    ):
        """Test filtering evaluators by type."""
        await evaluator_service.create_evaluator(sample_llm_judge_create)
        await evaluator_service.create_evaluator(sample_code_evaluator_create)

        llm_evaluators = await evaluator_service.get_evaluators(type_filter="llm_judge")
        code_evaluators = await evaluator_service.get_evaluators(type_filter="code")

        # Should include our test evaluator and potentially system ones
        assert any(e.name == "test_llm_judge" for e in llm_evaluators)
        assert any(e.name == "test_code_evaluator" for e in code_evaluators)

    @pytest.mark.asyncio
    async def test_set_task_evaluators(
        self,
        evaluator_service,
        db_session: AsyncSession,
        sample_llm_judge_create,
        sample_code_evaluator_create,
    ):
        """Test setting evaluators for a task."""
        from app.models.eval_task import EvalTask
        from app.models.case_set import CaseSet
        from app.models.model import Model
        import uuid

        # Create evaluator
        llm_eval = await evaluator_service.create_evaluator(sample_llm_judge_create)
        code_eval = await evaluator_service.create_evaluator(sample_code_evaluator_create)

        # Create test task
        case_set = CaseSet(name="Test Set")
        db_session.add(case_set)
        await db_session.flush()

        # Create a test model provider and model
        from app.models.model_provider import ModelProvider
        provider = ModelProvider(
            name="Test Provider",
            base_url="https://test.com",
            api_key="test_key"
        )
        db_session.add(provider)
        await db_session.flush()

        model = Model(
            provider_id=provider.id,
            model_code="test_model",
            display_name="Test Model"
        )
        db_session.add(model)
        await db_session.flush()

        task = EvalTask(
            set_id=case_set.id,
            model_id=model.id,
            request_template="{}"
        )
        db_session.add(task)
        await db_session.flush()

        # Set evaluators
        await evaluator_service.set_task_evaluators(
            task.id,
            [llm_eval.id, code_eval.id]
        )

        # Get task evaluators
        task_evaluators = await evaluator_service.get_task_evaluators(task.id)

        assert len(task_evaluators) == 2
        assert task_evaluators[0]["id"] == llm_eval.id
        assert task_evaluators[1]["id"] == code_eval.id
        assert task_evaluators[0]["order_index"] == 0
        assert task_evaluators[1]["order_index"] == 1

    @pytest.mark.asyncio
    async def test_get_default_evaluators(
        self,
        evaluator_service,
        db_session: AsyncSession,
    ):
        """Test getting default evaluators."""
        # Create default evaluators for testing
        exact_match = Evaluator(
            name="exact_match",
            description="Exact match evaluator",
            type="code",
            config='{"code": "def evaluate(e,a): return {\\\"result\\\": \\\"passed\\\"}"}',
            is_system=1,
        )
        json_compare = Evaluator(
            name="json_compare",
            description="JSON compare evaluator",
            type="code",
            config='{"code": "def evaluate(e,a): return {\\\"result\\\": \\\"passed\\\"}"}',
            is_system=1,
        )
        db_session.add(exact_match)
        db_session.add(json_compare)
        await db_session.flush()

        defaults = await evaluator_service.get_default_evaluators()

        # Should have exact_match and json_compare
        assert len(defaults) >= 2
        names = {e.name for e in defaults}
        assert "exact_match" in names
        assert "json_compare" in names
