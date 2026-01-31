"""Code Executor Evaluator - executes Python code for evaluation."""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Optional, Tuple

from app.evaluators.base import BaseEvaluator


class CodeEvaluator(BaseEvaluator):
    """Evaluator that executes Python code in a sandboxed environment."""

    def __init__(self, code: str):
        """Initialize Code evaluator.

        Args:
            code: Python code to execute
        """
        self.code = code

    @property
    def name(self) -> str:
        """Get evaluator name."""
        return "code_executor"

    def evaluate(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Evaluate using Python code execution.

        Args:
            expected: Expected output
            actual: Actual output from LLM

        Returns:
            Tuple of (is_passed, reason)
        """
        # This is a sync wrapper - actual async implementation in eval service
        # The actual evaluation will be done in the async eval service
        return False, "Code评估器需要在异步上下文中使用"

    async def evaluate_async(self, expected: str, actual: str) -> Tuple[bool, Optional[str]]:
        """Async evaluate using Python code execution in subprocess.

        Args:
            expected: Expected output
            actual: Actual output from LLM

        Returns:
            Tuple of (is_passed, reason)
        """
        # Create evaluation script
        script = f'''
import json

def evaluate(expected: str, actual: str) -> dict:
    """User-provided evaluation function."""
{self.code}

if __name__ == "__main__":
    import sys
    expected_val = sys.argv[1]
    actual_val = sys.argv[2]
    result = evaluate(expected_val, actual_val)
    print(json.dumps(result, ensure_ascii=False))
'''

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            script_path = f.name
            f.write(script)

        try:
            # Run in subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                'python',
                script_path,
                expected,
                actual,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, "代码执行超时（10秒限制）"

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                return False, f"代码执行失败: {error_msg}"

            # Parse output
            output = stdout.decode('utf-8', errors='replace').strip()
            try:
                result = json.loads(output)
                result_value = result.get("result", "failed").lower()
                reason = result.get("reason", "")

                if result_value == "passed":
                    return True, reason
                else:
                    return False, reason or "评估未通过"
            except json.JSONDecodeError:
                return False, f"代码输出无效JSON: {output[:200]}"

        finally:
            # Clean up temp file
            try:
                os.unlink(script_path)
            except OSError:
                pass
