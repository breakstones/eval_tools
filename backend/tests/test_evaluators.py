"""Tests for evaluator functionality."""

import pytest

from app.evaluators.exact_match import ExactMatchEvaluator
from app.evaluators.json_compare import JsonCompareEvaluator


class TestExactMatchEvaluator:
    """Tests for ExactMatchEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""
        return ExactMatchEvaluator()

    def test_name(self, evaluator):
        """Test evaluator name."""
        assert evaluator.name == "exact_match"

    def test_exact_match_pass(self, evaluator):
        """Test exact match passes."""
        passed, reason = evaluator.evaluate("hello world", "hello world")
        assert passed is True
        assert reason == "Exact match"

    def test_exact_match_fail(self, evaluator):
        """Test exact match fails."""
        passed, reason = evaluator.evaluate("hello", "world")
        assert passed is False
        assert "Mismatch" in reason

    def test_both_empty(self, evaluator):
        """Test both empty strings."""
        passed, reason = evaluator.evaluate("", "")
        assert passed is True
        assert reason == "Both empty"

    def test_empty_expected(self, evaluator):
        """Test empty expected output."""
        passed, reason = evaluator.evaluate("", "actual")
        assert passed is False
        assert "Expected output is empty" in reason

    def test_empty_actual(self, evaluator):
        """Test empty actual output."""
        passed, reason = evaluator.evaluate("expected", "")
        assert passed is False
        assert "Actual output is empty" in reason

    def test_whitespace_normalized(self, evaluator):
        """Test that whitespace is normalized."""
        passed, reason = evaluator.evaluate("hello  world\n\t", "hello world")
        assert passed is True


class TestJsonCompareEvaluator:
    """Tests for JsonCompareEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""
        return JsonCompareEvaluator()

    def test_name(self, evaluator):
        """Test evaluator name."""
        assert evaluator.name == "json_compare"

    def test_json_match_simple(self, evaluator):
        """Test simple JSON match."""
        passed, reason = evaluator.evaluate('{"key": "value"}', '{"key": "value"}')
        assert passed is True
        assert reason == "JSON structures match"

    def test_json_match_nested(self, evaluator):
        """Test nested JSON match."""
        expected = '{"user": {"name": "Alice", "age": 30}}'
        actual = '{"user": {"name": "Alice", "age": 30}}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is True

    def test_json_match_array(self, evaluator):
        """Test JSON array match."""
        expected = '{"items": [1, 2, 3]}'
        actual = '{"items": [1, 2, 3]}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is True

    def test_json_value_mismatch(self, evaluator):
        """Test JSON value mismatch."""
        expected = '{"key": "value1"}'
        actual = '{"key": "value2"}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is False
        assert "Value mismatch" in reason

    def test_json_missing_key(self, evaluator):
        """Test JSON missing key."""
        expected = '{"key1": "value1", "key2": "value2"}'
        actual = '{"key1": "value1"}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is False
        assert "Missing key" in reason

    def test_json_extra_key(self, evaluator):
        """Test JSON extra key."""
        expected = '{"key1": "value1"}'
        actual = '{"key1": "value1", "key2": "value2"}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is False
        assert "Extra key" in reason

    def test_json_type_mismatch(self, evaluator):
        """Test JSON type mismatch."""
        expected = '{"key": "string"}'
        actual = '{"key": 123}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is False
        assert "Type mismatch" in reason

    def test_json_array_length_mismatch(self, evaluator):
        """Test JSON array length mismatch."""
        expected = '{"items": [1, 2, 3]}'
        actual = '{"items": [1, 2]}'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is False
        assert "Length mismatch" in reason

    def test_parse_json_from_code_block(self, evaluator):
        """Test parsing JSON from markdown code block."""
        expected = '{"key": "value"}'
        actual = '```json\n{"key": "value"}\n```'
        passed, reason = evaluator.evaluate(expected, actual)
        assert passed is True

    def test_no_expected_json(self, evaluator):
        """Test when no expected JSON is provided."""
        passed, reason = evaluator.evaluate("", "some output")
        assert passed is True
        assert "No expected JSON" in reason

    def test_invalid_expected_json(self, evaluator):
        """Test when expected output is not valid JSON."""
        passed, reason = evaluator.evaluate("not json", '{"key": "value"}')
        assert passed is True
        assert "not valid JSON" in reason

    def test_invalid_actual_json(self, evaluator):
        """Test when actual output is not valid JSON."""
        passed, reason = evaluator.evaluate('{"key": "value"}', "not json")
        assert passed is False
        assert "not valid JSON" in reason
