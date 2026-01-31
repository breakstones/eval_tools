"""LLM API client for making asynchronous requests."""

import json
from typing import Any, Dict, Optional

import httpx


class LlmClient:
    """Client for making asynchronous LLM API requests."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 60) -> None:
        """Initialize LLM client.

        Args:
            base_url: Base URL for the LLM API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def call_llm(self, request_body: Dict[str, Any]) -> Optional[str]:
        """Call the LLM API with the given request body.

        Args:
            request_body: Request body to send to LLM API

        Returns:
            LLM response text or None if request fails

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        # Determine endpoint from request body
        model = request_body.get("model", "")
        messages = request_body.get("messages", [])

        # Build request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Try common endpoint patterns
        endpoints = [
            "/v1/chat/completions",
            "/chat/completions",
            "/api/chat",
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await client.post(url, json=request_body, headers=headers)

                    if response.status_code == 200:
                        data = response.json()

                        # Try to extract response text from common response formats
                        if "choices" in data and data["choices"]:
                            return data["choices"][0].get("message", {}).get("content", "")
                        elif "output" in data:
                            return data["output"]
                        elif "response" in data:
                            return data["response"]
                        elif "text" in data:
                            return data["text"]
                        elif isinstance(data, str):
                            return data
                        else:
                            return json.dumps(data, ensure_ascii=False)

                except httpx.HTTPError:
                    continue

            # All endpoints failed, try direct URL
            try:
                response = await client.post(
                    self.base_url,
                    json=request_body,
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0].get("message", {}).get("content", "")
                    return json.dumps(data, ensure_ascii=False)
            except httpx.HTTPError:
                pass

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
