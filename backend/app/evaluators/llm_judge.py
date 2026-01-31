"""LLM Judge Evaluator - uses LLM to evaluate outputs."""

import json
from typing import Optional, Tuple, Dict, Any

from app.evaluators.base import BaseEvaluator
from app.utils.llm_client import LlmClient


class LlmJudgeEvaluator(BaseEvaluator):
    """Evaluator that uses LLM to judge if output matches expected."""

    def __init__(self, config: Dict[str, Any], llm_client: LlmClient):
        """Initialize LLM Judge evaluator.

        Args:
            config: Configuration dict with prompt_template
            llm_client: LLM client for making requests
        """
        self.prompt_template = config.get("prompt_template", "")
        self.llm_client = llm_client

    @property
    def name(self) -> str:
        """Get evaluator name."""
        return "llm_judge"

    def evaluate(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Evaluate using LLM as judge.

        Args:
            expected: Expected output
            actual: Actual output from LLM

        Returns:
            Tuple of (is_passed, reason)
        """
        # Render prompt template
        prompt = self.prompt_template.format(expected=expected, actual=actual)

        # Create request for LLM
        request = {
            "model": self.llm_client.model_code,
            "messages": [
                {"role": "system", "content": "你是一个专业的评估助手。请以JSON格式返回评估结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        # This is a sync wrapper - actual async implementation in eval service
        # For now, return a placeholder result
        # The actual evaluation will be done in the async eval service
        return False, "LLM Judge评估器需要在异步上下文中使用"
