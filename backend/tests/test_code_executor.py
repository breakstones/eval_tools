"""Tests for Code Executor evaluator."""

import pytest

from app.evaluators.code_executor import CodeEvaluator


@pytest.fixture
def simple_match_code():
    """Simple code that checks if strings match."""
    return '''
def evaluate(expected: str, actual: str) -> dict:
    if expected == actual:
        return {"result": "passed", "reason": "匹配"}
    return {"result": "failed", "reason": "不匹配"}
'''


@pytest.fixture
def normalize_whitespace_code():
    """Code that normalizes whitespace before comparison."""
    return '''
def evaluate(expected: str, actual: str) -> dict:
    def normalize(s):
        return " ".join(s.split())
    if normalize(expected) == normalize(actual):
        return {"result": "passed", "reason": "归一化后匹配"}
    return {"result": "failed", "reason": "归一化后不匹配"}
'''


@pytest.fixture
def invalid_code():
    """Invalid Python code."""
    return '''
def evaluate(expected: str, actual: str) -> dict:
    this is invalid python syntax
    return {"result": "passed", "reason": "..."}
'''


@pytest.fixture
def timeout_code():
    """Code that will timeout."""
    return '''
import time
def evaluate(expected: str, actual: str) -> dict:
    time.sleep(20)  # Sleep longer than timeout
    return {"result": "passed", "reason": "..."}
'''


class TestCodeEvaluator:
    """Tests for CodeEvaluator class."""

    def test_name_property(self, simple_match_code):
        """Test evaluator name."""
        evaluator = CodeEvaluator(simple_match_code)
        assert evaluator.name == "code_executor"

    def test_init_with_code(self, simple_match_code):
        """Test initialization with code."""
        evaluator = CodeEvaluator(simple_match_code)
        assert evaluator.code == simple_match_code

    def test_evaluate_returns_placeholder(self, simple_match_code):
        """Test that sync evaluate returns placeholder."""
        evaluator = CodeEvaluator(simple_match_code)
        is_passed, reason = evaluator.evaluate("expected", "actual")

        # Sync evaluate should return placeholder result
        assert is_passed is False
        assert "异步上下文" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_passed(self, simple_match_code):
        """Test async evaluation with matching strings."""
        evaluator = CodeEvaluator(simple_match_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        assert is_passed is True
        assert "匹配" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_failed(self, simple_match_code):
        """Test async evaluation with non-matching strings."""
        evaluator = CodeEvaluator(simple_match_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Goodbye")

        assert is_passed is False
        assert "不匹配" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_with_normalization(self, normalize_whitespace_code):
        """Test async evaluation with whitespace normalization."""
        evaluator = CodeEvaluator(normalize_whitespace_code)
        is_passed, reason = await evaluator.evaluate_async(
            "Hello   World",
            "Hello World"
        )

        assert is_passed is True
        assert "归一化后匹配" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_with_invalid_code(self, invalid_code):
        """Test async evaluation with invalid Python code."""
        evaluator = CodeEvaluator(invalid_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        assert is_passed is False
        assert "代码执行失败" in reason or "SyntaxError" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_with_timeout(self, timeout_code):
        """Test async evaluation with code that times out."""
        evaluator = CodeEvaluator(timeout_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        assert is_passed is False
        assert "超时" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_with_invalid_json_output(self):
        """Test async evaluation when code returns invalid JSON."""
        invalid_json_code = '''
def evaluate(expected: str, actual: str) -> dict:
    print("This is not JSON")
    return "invalid"
'''
        evaluator = CodeEvaluator(invalid_json_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        assert is_passed is False
        assert "JSON" in reason

    @pytest.mark.asyncio
    async def test_evaluate_async_with_missing_result_field(self):
        """Test async evaluation when result field is missing."""
        missing_result_code = '''
def evaluate(expected: str, actual: str) -> dict:
    return {"reason": "test"}
'''
        evaluator = CodeEvaluator(missing_result_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        # Should handle missing result field gracefully
        assert is_passed is False  # default to failed when result is missing

    @pytest.mark.asyncio
    async def test_evaluate_async_with_passed_result(self):
        """Test async evaluation returns passed."""
        passed_code = '''
def evaluate(expected: str, actual: str) -> dict:
    return {"result": "PASSED", "reason": "test"}
'''
        evaluator = CodeEvaluator(passed_code)
        is_passed, reason = await evaluator.evaluate_async("Hello", "Hello")

        # Should handle case-insensitive "passed"
        assert is_passed is True

    @pytest.mark.asyncio
    async def test_evaluate_async_with_special_characters(self, simple_match_code):
        """Test async evaluation with special characters in input."""
        evaluator = CodeEvaluator(simple_match_code)
        special_input = "Hello\n\tWorld\\\"'"

        is_passed, reason = await evaluator.evaluate_async(special_input, special_input)

        assert is_passed is True
