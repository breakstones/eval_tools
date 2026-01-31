"""Tests for template rendering functionality."""

import json

import pytest

from app.utils.templater import TemplateRenderer


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    @pytest.fixture
    def renderer(self):
        """Create template renderer for testing."""
        return TemplateRenderer()

    def test_resolve_variable_simple(self, renderer):
        """Test resolving simple variable."""
        context = {"model_name": "gpt-4"}
        result = renderer._resolve_variable("model_name", context)
        assert result == "gpt-4"

    def test_resolve_variable_nested(self, renderer):
        """Test resolving nested variable."""
        context = {
            "case": {
                "user_input": "Hello world",
            }
        }
        result = renderer._resolve_variable("case.user_input", context)
        assert result == "Hello world"

    def test_resolve_variable_missing(self, renderer):
        """Test resolving missing variable."""
        context = {"model_name": "gpt-4"}
        result = renderer._resolve_variable("missing_var", context)
        assert result == ""

    def test_substitute_in_string(self, renderer):
        """Test substituting variables in string."""
        context = {"model_name": "gpt-4"}
        result = renderer._substitute_in_value("Model: ${model_name}", context)
        assert result == "Model: gpt-4"

    def test_substitute_multiple_variables(self, renderer):
        """Test substituting multiple variables in string."""
        context = {
            "model_name": "gpt-4",
            "case": {"user_input": "Hello"}
        }
        result = renderer._substitute_in_value(
            "${model_name}: ${case.user_input}",
            context
        )
        assert result == "gpt-4: Hello"

    def test_substitute_in_dict(self, renderer):
        """Test substituting variables in dict."""
        context = {"model_name": "gpt-4"}
        template = {
            "model": "${model_name}",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        result = renderer._substitute_in_value(template, context)
        assert result["model"] == "gpt-4"
        assert result["messages"][0]["role"] == "user"

    def test_substitute_in_list(self, renderer):
        """Test substituting variables in list."""
        context = {"case": {"user_input": "Hello"}}
        template = [
            {"role": "system", "content": "Help"},
            {"role": "user", "content": "${case.user_input}"}
        ]
        result = renderer._substitute_in_value(template, context)
        assert result[1]["content"] == "Hello"

    def test_render_request_template_success(self, renderer):
        """Test successful request template rendering."""
        template = {
            "model": "${model_name}",
            "messages": [
                {"role": "system", "content": "${case_set.system_prompt}"},
                {"role": "user", "content": "${case.user_input}"}
            ]
        }
        context = {
            "model_name": "gpt-4",
            "case_set": {"system_prompt": "You are helpful"},
            "case": {"user_input": "Hello"}
        }
        result = renderer.render_request_template(template, context)
        assert result["model"] == "gpt-4"
        assert result["messages"][0]["content"] == "You are helpful"
        assert result["messages"][1]["content"] == "Hello"

    def test_render_template_string_with_quotes(self, renderer):
        """Test rendering template string with quotes."""
        context = {"case": {"user_input": 'Say "Hello"'}}
        template = {"content": "${case.user_input}"}
        result = renderer.render_request_template(template, context)
        assert result["content"] == 'Say "Hello"'

    def test_render_template_string_with_newlines(self, renderer):
        """Test rendering template string with newlines."""
        context = {"case": {"user_input": "Line1\nLine2\nLine3"}}
        template = {"content": "${case.user_input}"}
        result = renderer.render_request_template(template, context)
        assert result["content"] == "Line1\nLine2\nLine3"

    def test_render_template_with_empty_system_prompt(self, renderer):
        """Test rendering with empty system prompt."""
        template = {
            "messages": [
                {"role": "system", "content": "${case_set.system_prompt}"},
                {"role": "user", "content": "${case.user_input}"}
            ]
        }
        context = {
            "case_set": {"system_prompt": ""},
            "case": {"user_input": "Hello"}
        }
        result = renderer.render_request_template(template, context)
        assert result["messages"][0]["content"] == ""
        assert result["messages"][1]["content"] == "Hello"

    def test_render_template_invalid_input(self, renderer):
        """Test rendering with invalid template input."""
        with pytest.raises(ValueError):
            renderer.render_request_template("not a dict", {})

    def test_render_template_string_simple(self, renderer):
        """Test render_template_string method."""
        context = {"name": "World"}
        result = renderer.render_template_string("Hello ${name}", context)
        assert result == "Hello World"
