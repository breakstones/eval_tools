"""Template rendering engine for LLM request templates."""

import json
import re
from typing import Any, Dict


class TemplateRenderer:
    """Renderer for LLM request templates with variable substitution."""

    # Pattern for ${variable} placeholders
    VARIABLE_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def _resolve_variable(
        self,
        var_path: str,
        context: Dict[str, Any],
    ) -> str:
        """Resolve a variable path to its value.

        Args:
            var_path: Variable path (e.g., 'case.user_input', 'model_name')
            context: Context dictionary containing variable values

        Returns:
            Resolved value as string

        Raises:
            KeyError: If variable path is not found in context
        """
        # Handle special top-level variables
        if var_path == "model_name":
            return str(context.get("model_name", ""))

        # Navigate nested paths
        parts = var_path.split(".")
        value: Any = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return ""

            if value is None:
                return ""

        return str(value) if value is not None else ""

    def _substitute_in_value(
        self,
        value: Any,
        context: Dict[str, Any],
    ) -> Any:
        """Recursively substitute variables in a value.

        Args:
            value: Value to substitute in
            context: Context dictionary

        Returns:
            Value with variables substituted
        """
        if isinstance(value, str):
            # Substitute variables in strings
            result = []
            last_end = 0

            for match in self.VARIABLE_PATTERN.finditer(value):
                # Add literal text before the variable
                result.append(value[last_end:match.start()])

                # Resolve and add the variable value
                var_path = match.group(1)
                resolved = self._resolve_variable(var_path, context)
                result.append(resolved)

                last_end = match.end()

            # Add remaining literal text
            result.append(value[last_end:])
            return "".join(result)

        elif isinstance(value, dict):
            # Recursively substitute in dict values
            return {k: self._substitute_in_value(v, context) for k, v in value.items()}

        elif isinstance(value, list):
            # Recursively substitute in list items
            return [self._substitute_in_value(item, context) for item in value]

        else:
            return value

    def render_request_template(
        self,
        template: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Render a request template with variable substitution.

        This method safely handles string values that may contain special characters
        (quotes, newlines) by building the dict structure first and then serializing.

        Args:
            template: Request template with ${variable} placeholders
            context: Context dictionary containing variable values

        Returns:
            Rendered request body ready for API call

        Raises:
            ValueError: If template is invalid
        """
        if not isinstance(template, dict):
            raise ValueError("Template must be a dictionary")

        # Perform deep substitution
        rendered = self._substitute_in_value(template, context)

        # Validate that the result is still a valid dict
        if not isinstance(rendered, dict):
            raise ValueError("Invalid template: result is not a dictionary after substitution")

        return rendered

    def render_template_string(
        self,
        template_str: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a simple template string.

        Args:
            template_str: Template string with ${variable} placeholders
            context: Context dictionary

        Returns:
            Rendered string
        """
        return self._substitute_in_value(template_str, context)
