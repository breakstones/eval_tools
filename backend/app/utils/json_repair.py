"""JSON repair utility for fixing malformed JSON from LLM outputs."""

import json
import re
from typing import Any, Optional


class JsonRepair:
    """Utility class for repairing malformed JSON strings."""

    @classmethod
    def repair(cls, json_str: str) -> Optional[str]:
        """Attempt to repair a malformed JSON string.

        Args:
            json_str: The malformed JSON string

        Returns:
            Repaired JSON string, or None if repair fails
        """
        if not json_str:
            return None

        # First, try to extract JSON from markdown code blocks
        json_str = cls._extract_json_from_markdown(json_str)

        # Try direct parse first
        if cls._is_valid_json(json_str):
            return json_str

        # Apply repair patterns in correct order
        repaired = json_str

        # Step 1: Fix common structural issues
        repaired = cls._fix_structural_issues(repaired)

        # Step 2: Fix quotes
        repaired = cls._fix_quotes(repaired)

        # Step 3: Fix keywords and values
        repaired = cls._fix_keywords_and_values(repaired)

        # Step 4: Final cleanup
        repaired = cls._final_cleanup(repaired)

        # Try to parse repaired string
        if cls._is_valid_json(repaired):
            return repaired

        # Try more aggressive repairs
        repaired = cls._aggressive_repair(repaired)
        if cls._is_valid_json(repaired):
            return repaired

        return None

    @classmethod
    def _fix_structural_issues(cls, json_str: str) -> str:
        """Fix structural JSON issues.

        Args:
            json_str: JSON string to fix

        Returns:
            Fixed JSON string
        """
        # Trailing commas in objects/arrays
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Extra commas before end of object/array
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # Missing commas between objects
        json_str = re.sub(r'([}\]])\s*([{[])', r'\1,\2', json_str)

        # Comments in JSON (// ...)
        json_str = re.sub(r'//.*?\n', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str)

        return json_str

    @classmethod
    def _fix_quotes(cls, json_str: str) -> str:
        """Fix quote issues in JSON.

        Args:
            json_str: JSON string to fix

        Returns:
            Fixed JSON string
        """
        # Missing quotes around property names (simple keys)
        # But avoid keys that are already quoted
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)

        return json_str

    @classmethod
    def _fix_keywords_and_values(cls, json_str: str) -> str:
        """Fix keyword and value issues in JSON.

        Args:
            json_str: JSON string to fix

        Returns:
            Fixed JSON string
        """
        # Fix boolean and null keywords BEFORE quote handling
        json_str = re.sub(r'\bNone\b', 'null', json_str)
        json_str = re.sub(r'\bTRUE\b', 'true', json_str)
        json_str = re.sub(r'\bFALSE\b', 'false', json_str)

        # Now handle single quotes - but be careful not to quote already quoted content
        # Only replace single quotes that are not part of double-quoted strings
        in_string = False
        result = []
        i = 0
        while i < len(json_str):
            c = json_str[i]
            if c == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
                result.append(c)
            elif not in_string and c == "'":
                # Check if this is a single-quoted string
                # Find the matching single quote
                j = i + 1
                while j < len(json_str) and json_str[j] != "'":
                    j += 1
                if j < len(json_str):
                    # Replace single quotes with double quotes
                    result.append('"')
                    result.append(json_str[i+1:j])
                    result.append('"')
                    i = j
                else:
                    result.append(c)
            else:
                result.append(c)
            i += 1

        json_str = ''.join(result)

        # Unquoted single-word string values (that aren't keywords or already fixed booleans)
        # This handles cases like: {name: John} -> {name: "John"}
        # But NOT: {active: true} -> should NOT become {active: "true"}
        keywords = {'true', 'false', 'null'}
        json_str = re.sub(
            r':\s*([a-zA-Z_][a-zA-Z0-9_]*)([,\s}])',
            lambda m: f': "{m.group(1)}"{m.group(2)}' if m.group(1).lower() not in keywords else f': {m.group(1)}{m.group(2)}',
            json_str
        )

        return json_str

    @classmethod
    def _final_cleanup(cls, json_str: str) -> str:
        """Final cleanup of JSON string.

        Args:
            json_str: JSON string to clean

        Returns:
            Cleaned JSON string
        """
        # Newlines in strings (should be \n)
        json_str = re.sub(r'"\s*\n\s*"', '', json_str)

        return json_str

    @classmethod
    def _extract_json_from_markdown(cls, text: str) -> str:
        """Extract JSON from markdown code blocks.

        Args:
            text: Text that may contain JSON in markdown blocks

        Returns:
            Extracted JSON or original text
        """
        # Try ```json...```
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try ```...```
        match = re.search(r'```\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1).strip()

        return text

    @classmethod
    def _is_valid_json(cls, json_str: str) -> bool:
        """Check if a string is valid JSON.

        Args:
            json_str: String to check

        Returns:
            True if valid JSON, False otherwise
        """
        if not json_str:
            return False
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    @classmethod
    def _aggressive_repair(cls, json_str: str) -> str:
        """Apply more aggressive JSON repair techniques.

        Args:
            json_str: The JSON string to repair

        Returns:
            Repaired JSON string
        """
        # Remove all control characters except newlines and tabs
        json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)

        # Try to balance brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        # Add missing closing braces
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)

        # Add missing closing brackets
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)

        return json_str

    @classmethod
    def repair_and_parse(cls, json_str: str) -> Optional[Any]:
        """Repair and parse a JSON string.

        Args:
            json_str: The potentially malformed JSON string

        Returns:
            Parsed JSON object, or None if repair and parse fail
        """
        repaired = cls.repair(json_str)
        if repaired:
            try:
                return json.loads(repaired)
            except (json.JSONDecodeError, ValueError):
                pass
        return None
