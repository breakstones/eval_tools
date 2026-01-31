"""Tests for JSON repair utility."""

import pytest

from app.utils.json_repair import JsonRepair


class TestJsonRepair:
    """Test cases for JsonRepair utility."""

    def test_repair_valid_json(self):
        """Valid JSON should pass through unchanged."""
        json_str = '{"name": "test", "value": 123}'
        result = JsonRepair.repair(json_str)
        assert result == json_str

    def test_repair_trailing_comma_object(self):
        """Repair trailing comma in object."""
        json_str = '{"name": "test", "value": 123,}'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '"value": 123}' in result
        assert ',}' not in result

    def test_repair_trailing_comma_array(self):
        """Repair trailing comma in array."""
        json_str = '[1, 2, 3,]'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '3]' in result
        assert ',]' not in result

    def test_repair_single_quotes(self):
        """Repair single quotes to double quotes."""
        json_str = "{'name': 'test', 'value': 123}"
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '"name"' in result
        assert '"test"' in result

    def test_repair_unquoted_keys(self):
        """Repair unquoted property names."""
        json_str = '{name: "test", value: 123}'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '"name"' in result
        assert '"value"' in result

    def test_repair_unquoted_string_values(self):
        """Repair unquoted string values."""
        json_str = '{"name": test, "active": true}'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '"test"' in result

    def test_repair_none_null(self):
        """Repair None to null."""
        json_str = '{"name": None, "value": 123}'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert 'null' in result

    def test_repair_true_false_lowercase(self):
        """Repair TRUE/FALSE to true/false."""
        json_str = '{"active": TRUE, "inactive": FALSE}'
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert 'true' in result
        assert 'false' in result

    def test_extract_json_from_markdown_code_block(self):
        """Extract JSON from markdown code block."""
        json_str = '''```json
{"name": "test", "value": 123}
```'''
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '{"name": "test"' in result

    def test_extract_json_from_plain_code_block(self):
        """Extract JSON from plain markdown code block."""
        json_str = '''```
{"name": "test"}
```'''
        result = JsonRepair.repair(json_str)
        assert result is not None
        assert '{"name": "test"}' in result

    def test_repair_missing_braces(self):
        """Repair missing closing braces."""
        json_str = '{"name": "test", "value": 123'
        result = JsonRepair.repair(json_str)
        assert result is not None
        # Should add missing closing brace
        assert result.rstrip().endswith('}')

    def test_repair_missing_brackets(self):
        """Repair missing closing brackets."""
        json_str = '[1, 2, 3'
        result = JsonRepair.repair(json_str)
        assert result is not None
        # Should add missing closing bracket
        assert result.rstrip().endswith(']')

    def test_repair_and_parse(self):
        """Test repair_and_parse method."""
        json_str = '{"name": "test", "value": 123,}'
        result = JsonRepair.repair_and_parse(json_str)
        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_repair_and_parse_fails_on_invalid(self):
        """Test repair_and_parse returns None for unfixable JSON."""
        json_str = 'this is not json at all'
        result = JsonRepair.repair_and_parse(json_str)
        assert result is None

    def test_repair_complex_nested_json(self):
        """Test repair of complex nested JSON."""
        json_str = '''{
            "user": {
                "name": "John",
                "age": 30,
                "hobbies": ["reading", "swimming",],
            },
        }'''
        result = JsonRepair.repair(json_str)
        assert result is not None
        parsed = JsonRepair.repair_and_parse(result)
        assert parsed is not None
        assert parsed["user"]["name"] == "John"
        assert parsed["user"]["hobbies"][0] == "reading"

    def test_repair_mixed_issues(self):
        """Test JSON with multiple issues."""
        json_str = "{name: 'test', value: 123, active: TRUE,}"
        result = JsonRepair.repair(json_str)
        assert result is not None
        parsed = JsonRepair.repair_and_parse(result)
        assert parsed is not None
        assert parsed["name"] == "test"
        assert parsed["value"] == 123
        assert parsed["active"] is True
