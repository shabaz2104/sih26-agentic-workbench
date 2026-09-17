"""HTTP adapter for OpenAI-compatible chat-completions servers."""

import json
import os
import socket
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..contracts import GenerationRequest, ModelConfig
from ..errors import (
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenAICompatibleProvider:
    """Generate text through an OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self._opener = opener

    def generate(self, request: GenerationRequest, config: ModelConfig) -> str:
        """Send a request and return the assistant message text."""
        if not config.endpoint.strip():
            raise ProviderResponseError("The provider endpoint must not be empty")

        payload = self._build_payload(request, config)
        http_request = Request(
            self._completion_url(config.endpoint),
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )

        try:
            with self._opener(http_request, timeout=config.timeout_seconds) as response:
                response_body = response.read()
        except (socket.timeout, TimeoutError) as error:
            raise ProviderTimeoutError("The model provider timed out") from error
        except (HTTPError, URLError, ConnectionError, OSError) as error:
            raise ProviderUnavailableError("The model provider is unavailable") from error

        return self._parse_response(response_body)

    @staticmethod
    def _build_payload(request: GenerationRequest, config: ModelConfig) -> dict[str, object]:
        messages: list[dict[str, str]] = []
        if request.system_prompt is not None:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, object] = {
            "model": config.model,
            "messages": messages,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @staticmethod
    def _completion_url(endpoint: str) -> str:
        normalized_endpoint = endpoint.rstrip("/")
        if normalized_endpoint.endswith("/chat/completions"):
            return normalized_endpoint
        return f"{normalized_endpoint}/v1/chat/completions"

    @staticmethod
    def _parse_response(response_body: bytes) -> str:
        try:
            response = json.loads(response_body)
            text = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ProviderResponseError("The provider returned a malformed response") from error

        if not isinstance(text, str):
            raise ProviderResponseError("The provider response content must be text")
        return text