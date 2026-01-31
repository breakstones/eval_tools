"""JSON comparison evaluator."""

import json
from typing import Any, List, Tuple, Optional

from app.evaluators.base import BaseEvaluator
from app.utils.json_repair import JsonRepair


class JsonCompareEvaluator(BaseEvaluator):
    """Evaluator that compares JSON structures."""

    @property
    def name(self) -> str:
        """Get evaluator name."""
        return "json_compare"

    def _parse_json(self, text: str) -> Tuple[Optional[Any], Optional[str]]:
        """Try to parse JSON from text, with repair attempts.

        Args:
            text: Text to parse

        Returns:
            Tuple of (parsed_json, repaired_json_string)
        """
        text = text.strip()
        if not text:
            return None, None

        # Try direct JSON parse
        try:
            return json.loads(text), text
        except json.JSONDecodeError:
            pass

        # Try to repair the JSON
        repaired = JsonRepair.repair(text)
        if repaired:
            try:
                return json.loads(repaired), repaired
            except json.JSONDecodeError:
                pass

        return None, None

    def _deep_compare(self, expected: Any, actual: Any, path: str = "") -> List[str]:
        """Deep compare two values.

        Args:
            expected: Expected value
            actual: Actual value
            path: Current path for error messages

        Returns:
            List of difference descriptions
        """
        differences: List[str] = []

        if type(expected) != type(actual):
            differences.append(f"{path}: Type mismatch - expected {type(expected).__name__}, got {type(actual).__name__}")
            return differences

        if isinstance(expected, dict):
            expected_keys = set(expected.keys())
            actual_keys = set(actual.keys())

            # Check for missing keys
            for key in expected_keys - actual_keys:
                differences.append(f"{path}.{key}: Missing key")

            # Check for extra keys
            for key in actual_keys - expected_keys:
                differences.append(f"{path}.{key}: Extra key")

            # Compare common keys
            for key in expected_keys & actual_keys:
                differences.extend(
                    self._deep_compare(expected[key], actual[key], f"{path}.{key}" if path else key)
                )

        elif isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append(f"{path}: Length mismatch - expected {len(expected)}, got {len(actual)}")
            else:
                for i, (e, a) in enumerate(zip(expected, actual)):
                    differences.extend(self._deep_compare(e, a, f"{path}[{i}]"))

        else:
            if expected != actual:
                differences.append(f"{path}: Value mismatch - expected {expected}, got {actual}")

        return differences

    def evaluate(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Evaluate JSON structure comparison.

        Args:
            expected: Expected output (JSON string)
            actual: Actual output (JSON string)

        Returns:
            Tuple of (is_passed, reason)
        """
        if not expected:
            # If no expected output, skip JSON comparison
            return True, "No expected JSON to compare"

        # Parse expected JSON
        try:
            expected_obj = json.loads(expected)
        except json.JSONDecodeError:
            return True, "Expected output is not valid JSON, skipping JSON comparison"

        # Parse actual JSON with repair
        actual_obj, repaired_actual = self._parse_json(actual)

        if actual_obj is None:
            return False, "Actual output is not valid JSON (repair failed)"

        # Check if repair was performed
        repair_note = ""
        if repaired_actual and repaired_actual != actual:
            repair_note = " (JSON was repaired)"

        differences = self._deep_compare(expected_obj, actual_obj)

        if not differences:
            return True, f"JSON structures match{repair_note}"

        return False, f"{'; '.join(differences[:5])}{repair_note}"  # Limit to first 5 differences
