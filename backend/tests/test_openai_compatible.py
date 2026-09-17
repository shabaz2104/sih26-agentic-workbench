import json
import socket
from typing import Any
from urllib.error import URLError

import pytest

from backend.src.model_access.contracts import GenerationRequest, ModelConfig
from backend.src.model_access.errors import (
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from backend.src.model_access.providers.openai_compatible import OpenAICompatibleProvider


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def successful_body(text: str = "generated answer") -> bytes:
    return json.dumps({"choices": [{"message": {"content": text}}]}).encode()


def test_provider_builds_expected_payload_and_parses_response() -> None:
    captured: dict[str, Any] = {}

    def opener(http_request: Any, timeout: float) -> FakeHTTPResponse:
        captured["url"] = http_request.full_url
        captured["headers"] = dict(http_request.headers)
        captured["payload"] = json.loads(http_request.data)
        captured["timeout"] = timeout
        return FakeHTTPResponse(successful_body())

    provider = OpenAICompatibleProvider(api_key="test-key", opener=opener)
    config = ModelConfig(
        provider="openai-compatible",
        model="local-coder",
        endpoint="http://model-server:8000",
        timeout_seconds=12.5,
    )
    request = GenerationRequest(
        prompt="Write a parser",
        system_prompt="You are a coding assistant.",
        temperature=0.2,
        max_tokens=128,
    )

    result = provider.generate(request, config)

    assert result == "generated answer"
    assert captured["url"] == "http://model-server:8000/v1/chat/completions"
    assert captured["timeout"] == 12.5
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"] == {
        "model": "local-coder",
        "messages": [
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": "Write a parser"},
        ],
        "temperature": 0.2,
        "max_tokens": 128,
    }


def test_provider_omits_optional_fields_and_accepts_completion_endpoint() -> None:
    captured: dict[str, Any] = {}

    def opener(http_request: Any, timeout: float) -> FakeHTTPResponse:
        captured["url"] = http_request.full_url
        captured["payload"] = json.loads(http_request.data)
        return FakeHTTPResponse(successful_body())

    provider = OpenAICompatibleProvider(opener=opener)
    config = ModelConfig(
        provider="openai-compatible",
        model="general-model",
        endpoint="http://model-server/v1/chat/completions",
    )

    provider.generate(GenerationRequest("Explain this"), config)

    assert captured["url"] == "http://model-server/v1/chat/completions"
    assert captured["payload"] == {
        "model": "general-model",
        "messages": [{"role": "user", "content": "Explain this"}],
    }


def test_connection_failure_becomes_provider_unavailable() -> None:
    def opener(*_: Any, **__: Any) -> None:
        raise URLError("connection refused")

    provider = OpenAICompatibleProvider(opener=opener)

    with pytest.raises(ProviderUnavailableError):
        provider.generate(GenerationRequest("Hello"), ModelConfig("provider", "model", "http://server"))


def test_timeout_becomes_provider_timeout() -> None:
    def opener(*_: Any, **__: Any) -> None:
        raise socket.timeout("timed out")

    provider = OpenAICompatibleProvider(opener=opener)

    with pytest.raises(ProviderTimeoutError):
        provider.generate(GenerationRequest("Hello"), ModelConfig("provider", "model", "http://server"))


@pytest.mark.parametrize(
    "body",
    [b"not json", b'{"choices": []}', b'{"choices": [{"message": {}}]}'],
)
def test_malformed_response_becomes_provider_response_error(body: bytes) -> None:
    provider = OpenAICompatibleProvider(opener=lambda *_args, **_kwargs: FakeHTTPResponse(body))

    with pytest.raises(ProviderResponseError):
        provider.generate(GenerationRequest("Hello"), ModelConfig("provider", "model", "http://server"))