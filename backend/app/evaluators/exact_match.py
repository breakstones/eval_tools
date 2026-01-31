"""Exact match evaluator."""

from typing import Tuple, Optional

from app.evaluators.base import BaseEvaluator


class ExactMatchEvaluator(BaseEvaluator):
    """Evaluator that checks for exact string match."""

    @property
    def name(self) -> str:
        """Get evaluator name."""
        return "exact_match"

    def evaluate(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Evaluate exact string match.

        Args:
            expected: Expected output
            actual: Actual output

        Returns:
            Tuple of (is_passed, reason)
        """
        if not expected and not actual:
            return True, "Both empty"

        if not expected:
            return False, "Expected output is empty"

        if not actual:
            return False, "Actual output is empty"

        # Normalize whitespace for comparison
        expected_normalized = " ".join(expected.split())
        actual_normalized = " ".join(actual.split())

        if expected_normalized == actual_normalized:
            return True, "Exact match"

        return False, f"Mismatch: expected '{expected}', got '{actual}'"
