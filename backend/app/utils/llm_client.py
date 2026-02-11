"""LLM API client for making asynchronous requests."""

import json
import sys
import time
import traceback
from typing import Any, Dict, Optional, Tuple

import httpx


class LlmCallResult:
    """Result of an LLM API call."""

    def __init__(
        self,
        content: Optional[str],
        duration_ms: int,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ):
        """Initialize LLM call result.

        Args:
            content: Response content
            duration_ms: Call duration in milliseconds
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            total_tokens: Total tokens used
        """
        self.content = content
        self.duration_ms = duration_ms
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens if total_tokens is not None else (
            (prompt_tokens or 0) + (completion_tokens or 0)
        )


class LlmClient:
    """Client for making asynchronous LLM API requests."""

    def __init__(self, base_url: str, api_key: str, endpoint: str = "", timeout: int = 60) -> None:
        """Initialize LLM client.

        Args:
            base_url: Base URL for LLM API
            api_key: API key for authentication
            endpoint: API endpoint path (e.g., "/chat/completions"), empty for default "/chat/completions"
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.endpoint = endpoint or "/chat/completions"
        self.timeout = timeout
        self.model_code: str = ""  # Set when making a request

    async def call_llm(self, request_body: Dict[str, Any]) -> Optional[str]:
        """Call the LLM API with the given request body.

        Args:
            request_body: Request body to send to LLM API

        Returns:
            LLM response text or None if request fails

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        result = await self.call_llm_with_stats(request_body)
        return result.content if result else None

    async def call_llm_with_stats(
        self, request_body: Dict[str, Any]
    ) -> Optional[LlmCallResult]:
        """Call the LLM API with the given request body and return statistics.

        Args:
            request_body: Request body to send to LLM API

        Returns:
            LlmCallResult with content, duration, and token usage, or None if request fails

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        # Set model code from request body
        self.model_code = request_body.get("model", "")

        # Build request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Use configured endpoint or default "/chat/completions"
        url = f"{self.base_url}{self.endpoint}"
        start_time = time.time()

        print(f"[DEBUG] LLM客户端请求, url={url}, model={self.model_code}", file=sys.stderr)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=request_body, headers=headers)

                if response.status_code == 200:
                    duration_ms = int((time.time() - start_time) * 1000)
                    try:
                        data = response.json()
                    except Exception as e:
                        # Failed to parse JSON response
                        print(f"[ERROR] LLM客户端JSON解析失败: {type(e).__name__}: {e}", file=sys.stderr)
                        print(f"[ERROR] 响应内容: {response.text[:500]}", file=sys.stderr)
                        return LlmCallResult(
                            content=f"[JSON_PARSE_ERROR] {response.text[:500]}",
                            duration_ms=duration_ms,
                        )

                    # Extract token usage if available
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
                    total_tokens = usage.get("total_tokens")

                    # Try to extract response text from common response formats
                    choices = data.get("choices")
                    if choices and len(choices) > 0:
                        message = choices[0].get("message") or {}
                        content = message.get("content")
                        if content:
                            return LlmCallResult(
                                content=str(content),
                                duration_ms=duration_ms,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                            )
                    elif "output" in data:
                        return LlmCallResult(
                            content=str(data.get("output", "")),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
                    elif "response" in data:
                        return LlmCallResult(
                            content=str(data.get("response", "")),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
                    elif "text" in data:
                        return LlmCallResult(
                            content=str(data.get("text", "")),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
                    elif "content" in data:
                        return LlmCallResult(
                            content=str(data.get("content", "")),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
                    elif "message" in data:
                        msg = data.get("message", {})
                        if isinstance(msg, dict):
                            return LlmCallResult(
                                content=str(msg.get("content", str(msg))),
                                duration_ms=duration_ms,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                            )
                        return LlmCallResult(
                            content=str(msg),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
                    else:
                        # Return raw JSON as fallback
                        return LlmCallResult(
                            content=json.dumps(data, ensure_ascii=False),
                            duration_ms=duration_ms,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                        )
            except httpx.HTTPError as e:
                print(f"[ERROR] LLM客户端HTTP错误: {type(e).__name__}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] LLM客户端异常: {type(e).__name__}: {e}", file=sys.stderr)
                import traceback
                print(f"[ERROR] 异常堆栈: {traceback.format_exc()}", file=sys.stderr)

        # 请求失败，返回 None
        print(f"[ERROR] LLM客户端请求失败，url={url}", file=sys.stderr)
        return None


class MockLlmClient(LlmClient):
    """Mock LLM client for testing."""

    def __init__(self) -> None:
        """Initialize mock client."""
        super().__init__("http://mock", "mock")

    async def call_llm(self, request_body: Dict[str, Any]) -> Optional[str]:
        """Return a mock response.

        Args:
            request_body: Request body (ignored in mock)

        Returns:
            Mock response
        """
        messages = request_body.get("messages", [])
        if messages:
            user_message = next(
                (m.get("content", "") for m in messages if m.get("role") == "user"),
                "",
            )
            return f"Mock response to: {user_message[:50]}..."
        return "Mock response"
