"""Base evaluator class and result types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class EvaluationResult:
    """Result of an evaluation."""

    passed: bool
    reason: Optional[str] = None


class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the evaluator name."""
        pass

    @abstractmethod
    def evaluate(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Evaluate expected vs actual output.

        Args:
            expected: Expected output
            actual: Actual output from LLM

        Returns:
            Tuple of (is_passed, reason)
        """
        pass
