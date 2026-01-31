"""Service for evaluator management."""

import json
from typing import List, Optional, Dict, Any
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.evaluator import Evaluator
from app.models.task_evaluator import TaskEvaluator
from app.models.eval_task import EvalTask
from app.schemas.evaluator import (
    EvaluatorCreate,
    EvaluatorUpdate,
    EvaluatorResponse,
)


class EvaluatorService:
    """Service for managing evaluators."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Database session
        """
        self.session = session

    @classmethod
    async def create(cls, session: AsyncSession) -> Self:
        """Create a new service instance.

        Args:
            session: Database session

        Returns:
            EvaluatorService instance
        """
        return cls(session)

    async def get_evaluators(
        self,
        type_filter: Optional[str] = None,
    ) -> List[Evaluator]:
        """Get all evaluators.

        Args:
            type_filter: Optional filter by evaluator type

        Returns:
            List of evaluators
        """
        query = select(Evaluator).order_by(Evaluator.created_at.desc())
        if type_filter:
            query = query.where(Evaluator.type == type_filter)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_evaluator(self, evaluator_id: str) -> Optional[Evaluator]:
        """Get an evaluator by ID.

        Args:
            evaluator_id: Evaluator ID

        Returns:
            Evaluator or None if not found
        """
        result = await self.session.execute(
            select(Evaluator).where(Evaluator.id == evaluator_id)
        )
        return result.scalar_one_or_none()

    async def get_evaluator_by_name(self, name: str) -> Optional[Evaluator]:
        """Get an evaluator by name.

        Args:
            name: Evaluator name

        Returns:
            Evaluator or None if not found
        """
        result = await self.session.execute(
            select(Evaluator).where(Evaluator.name == name)
        )
        return result.scalar_one_or_none()

    async def create_evaluator(self, data: EvaluatorCreate) -> Evaluator:
        """Create a new evaluator.

        Args:
            data: Evaluator creation data

        Returns:
            Created evaluator

        Raises:
            ValueError: If evaluator name already exists
        """
        # Check if name already exists
        existing = await self.get_evaluator_by_name(data.name)
        if existing:
            raise ValueError(f"评估器名称已存在: {data.name}")

        # Validate type-specific config
        if data.type == "llm_judge":
            if "prompt_template" not in data.config:
                raise ValueError("LLM评估器必须配置 prompt_template")
        elif data.type == "code":
            if "code" not in data.config:
                raise ValueError("代码评估器必须配置 code")

        evaluator = Evaluator(
            name=data.name,
            description=data.description,
            type=data.type,
            config=json.dumps(data.config, ensure_ascii=False),
            is_system=0,
        )
        self.session.add(evaluator)
        await self.session.flush()
        await self.session.refresh(evaluator)
        return evaluator

    async def update_evaluator(
        self,
        evaluator_id: str,
        data: EvaluatorUpdate,
    ) -> Evaluator:
        """Update an evaluator.

        Args:
            evaluator_id: Evaluator ID
            data: Update data

        Returns:
            Updated evaluator

        Raises:
            ValueError: If evaluator not found or is system evaluator
        """
        evaluator = await self.get_evaluator(evaluator_id)
        if evaluator is None:
            raise ValueError(f"评估器不存在: {evaluator_id}")

        if evaluator.is_system:
            raise ValueError("不能修改系统内置评估器")

        if data.name is not None:
            existing = await self.get_evaluator_by_name(data.name)
            if existing and existing.id != evaluator_id:
                raise ValueError(f"评估器名称已存在: {data.name}")
            evaluator.name = data.name

        if data.description is not None:
            evaluator.description = data.description

        if data.config is not None:
            # Validate type-specific config
            if evaluator.type == "llm_judge":
                if "prompt_template" not in data.config:
                    raise ValueError("LLM评估器必须配置 prompt_template")
            elif evaluator.type == "code":
                if "code" not in data.config:
                    raise ValueError("代码评估器必须配置 code")
            evaluator.config_dict = data.config

        await self.session.flush()
        await self.session.refresh(evaluator)
        return evaluator

    async def delete_evaluator(self, evaluator_id: str) -> bool:
        """Delete an evaluator.

        Args:
            evaluator_id: Evaluator ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If evaluator is system evaluator
        """
        evaluator = await self.get_evaluator(evaluator_id)
        if evaluator is None:
            return False

        if evaluator.is_system:
            raise ValueError("不能删除系统内置评估器")

        await self.session.execute(
            delete(Evaluator).where(Evaluator.id == evaluator_id)
        )
        return True

    async def get_task_evaluators(self, task_id: str) -> List[Dict[str, Any]]:
        """Get evaluators for a task.

        Args:
            task_id: Task ID

        Returns:
            List of evaluator info with order
        """
        result = await self.session.execute(
            select(TaskEvaluator, Evaluator)
            .join(Evaluator, TaskEvaluator.evaluator_id == Evaluator.id)
            .where(TaskEvaluator.task_id == task_id)
            .order_by(TaskEvaluator.order_index)
        )
        evaluators = []
        for task_eval, evaluator in result.all():
            evaluators.append({
                "id": evaluator.id,
                "name": evaluator.name,
                "description": evaluator.description,
                "type": evaluator.type,
                "config": evaluator.config_dict,
                "is_system": bool(evaluator.is_system),
                "order_index": task_eval.order_index,
            })
        return evaluators

    async def set_task_evaluators(
        self,
        task_id: str,
        evaluator_ids: List[str],
    ) -> None:
        """Set evaluators for a task.

        Args:
            task_id: Task ID
            evaluator_ids: List of evaluator IDs in order

        Raises:
            ValueError: If task or evaluator not found
        """
        # Verify task exists
        task_result = await self.session.execute(
            select(EvalTask).where(EvalTask.id == task_id)
        )
        task = task_result.scalar_one_or_none()
        if task is None:
            raise ValueError(f"任务不存在: {task_id}")

        # Verify all evaluators exist
        for eval_id in evaluator_ids:
            eval_result = await self.session.execute(
                select(Evaluator).where(Evaluator.id == eval_id)
            )
            evaluator = eval_result.scalar_one_or_none()
            if evaluator is None:
                raise ValueError(f"评估器不存在: {eval_id}")

        # Delete existing task evaluators
        await self.session.execute(
            delete(TaskEvaluator).where(TaskEvaluator.task_id == task_id)
        )

        # Add new task evaluators
        for index, eval_id in enumerate(evaluator_ids):
            task_eval = TaskEvaluator(
                task_id=task_id,
                evaluator_id=eval_id,
                order_index=index,
            )
            self.session.add(task_eval)

    async def get_default_evaluators(self) -> List[Evaluator]:
        """Get default evaluators for tasks without explicit configuration.

        Returns:
            List of default evaluators (exact_match, json_compare)
        """
        result = await self.session.execute(
            select(Evaluator).where(
                Evaluator.name.in_(["exact_match", "json_compare"])
            )
        )
        return list(result.scalars().all())
