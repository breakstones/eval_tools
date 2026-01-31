"""Tests for LLM Judge evaluator."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.evaluators.llm_judge import LlmJudgeEvaluator
from app.utils.llm_client import LlmClient


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock(spec=LlmClient)
    client.model_code = "gpt-4"
    client.call_llm = AsyncMock()
    return client


@pytest.fixture
def sample_config():
    """Sample LLM judge configuration."""
    return {
        "prompt_template": """Evaluate the following:

Expected: {expected}
Actual: {actual}

Return JSON: {{"result": "passed"|"failed", "reason": "..."}}"""
    }


class TestLlmJudgeEvaluator:
    """Tests for LlmJudgeEvaluator class."""

    def test_name_property(self, sample_config, mock_llm_client):
        """Test evaluator name."""
        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)
        assert evaluator.name == "llm_judge"

    def test_init_with_config(self, sample_config, mock_llm_client):
        """Test initialization with configuration."""
        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)
        assert evaluator.prompt_template == sample_config["prompt_template"]
        assert evaluator.llm_client == mock_llm_client

    def test_init_with_default_prompt(self, mock_llm_client):
        """Test initialization with default empty prompt."""
        evaluator = LlmJudgeEvaluator({}, mock_llm_client)
        assert evaluator.prompt_template == ""

    def test_evaluate_returns_placeholder(self, sample_config, mock_llm_client):
        """Test that sync evaluate returns placeholder."""
        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)
        is_passed, reason = evaluator.evaluate("expected", "actual")

        # Sync evaluate should return placeholder result
        assert is_passed is False
        assert "异步上下文" in reason

    @pytest.mark.asyncio
    async def test_full_evaluation_flow(self, sample_config, mock_llm_client):
        """Test full evaluation flow with async LLM call."""
        # Mock the LLM response
        mock_llm_client.call_llm.return_value = json.dumps({
            "result": "passed",
            "reason": "输出匹配预期"
        })

        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)

        # Simulate the async evaluation flow that would happen in eval service
        prompt = evaluator.prompt_template.format(
            expected="Hello World",
            actual="Hello World"
        )

        request = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一个专业的评估助手。请以JSON格式返回评估结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        response = await mock_llm_client.call_llm(request)
        result = json.loads(response)

        assert result["result"] == "passed"
        assert result["reason"] == "输出匹配预期"

    @pytest.mark.asyncio
    async def test_evaluation_with_failed_result(self, sample_config, mock_llm_client):
        """Test evaluation with failed result."""
        mock_llm_client.call_llm.return_value = json.dumps({
            "result": "failed",
            "reason": "输出不匹配"
        })

        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)

        prompt = evaluator.prompt_template.format(
            expected="Hello",
            actual="Goodbye"
        )

        request = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一个专业的评估助手。请以JSON格式返回评估结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        response = await mock_llm_client.call_llm(request)
        result = json.loads(response)

        assert result["result"] == "failed"
        assert "不匹配" in result["reason"]

    @pytest.mark.asyncio
    async def test_evaluation_with_invalid_json(self, sample_config, mock_llm_client):
        """Test evaluation when LLM returns invalid JSON."""
        mock_llm_client.call_llm.return_value = "This is not valid JSON"

        evaluator = LlmJudgeEvaluator(sample_config, mock_llm_client)

        prompt = evaluator.prompt_template.format(
            expected="Hello",
            actual="Hello"
        )

        request = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一个专业的评估助手。请以JSON格式返回评估结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

        response = await mock_llm_client.call_llm(request)

        # Should handle JSON parsing error
        try:
            result = json.loads(response)
            is_passed = result.get("result", "failed").lower() == "passed"
        except json.JSONDecodeError:
            is_passed = False

        assert is_passed is False
