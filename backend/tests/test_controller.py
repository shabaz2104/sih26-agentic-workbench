import pytest

from backend.src.model_access.classifier import KeywordTaskClassifier
from backend.src.model_access.contracts import GenerationRequest, ModelConfig, TaskType
from backend.src.model_access.controller import ModelAccessController
from backend.src.model_access.errors import (
    InvalidRequestError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RouteNotConfiguredError,
)
from backend.src.model_access.routing import ModelRouter


class FakeProvider:
    def __init__(self, response: str = "fake response") -> None:
        self.response = response
        self.calls: list[tuple[GenerationRequest, ModelConfig]] = []

    def generate(self, request: GenerationRequest, config: ModelConfig) -> str:
        self.calls.append((request, config))
        return self.response


class UnavailableProvider(FakeProvider):
    def generate(self, request: GenerationRequest, config: ModelConfig) -> str:
        raise ConnectionError("server unavailable")


class TimeoutProvider(FakeProvider):
    def generate(self, request: GenerationRequest, config: ModelConfig) -> str:
        raise TimeoutError("request timed out")


def make_controller(provider: FakeProvider, routes: dict[TaskType, ModelConfig]) -> ModelAccessController:
    return ModelAccessController(
        classifier=KeywordTaskClassifier(),
        router=ModelRouter(routes),
        provider=provider,
    )


def test_coding_request_selects_coding_route_and_normalizes_response() -> None:
    provider = FakeProvider("generated code")
    coding_config = ModelConfig(provider="fake", model="coding-model")
    controller = make_controller(provider, {TaskType.CODING: coding_config})

    response = controller.generate(GenerationRequest("Write a Python function"))

    assert response.text == "generated code"
    assert response.task_type == TaskType.CODING
    assert response.provider == "fake"
    assert response.model == "coding-model"
    assert provider.calls[0][1] == coding_config


def test_general_request_selects_general_route() -> None:
    provider = FakeProvider()
    general_config = ModelConfig(provider="fake", model="general-model")
    controller = make_controller(provider, {TaskType.GENERAL: general_config})

    response = controller.generate(GenerationRequest("Explain retrieval augmented generation"))

    assert response.task_type == TaskType.GENERAL
    assert provider.calls[0][1] == general_config


def test_explicit_task_type_overrides_classifier() -> None:
    provider = FakeProvider()
    general_config = ModelConfig(provider="fake", model="general-model")
    controller = make_controller(provider, {TaskType.GENERAL: general_config})

    response = controller.generate(
        GenerationRequest("Write a Python function", task_type=TaskType.GENERAL)
    )

    assert response.task_type == TaskType.GENERAL
    assert provider.calls[0][1] == general_config


def test_empty_prompt_is_rejected() -> None:
    provider = FakeProvider()
    controller = make_controller(provider, {})

    with pytest.raises(InvalidRequestError):
        controller.generate(GenerationRequest("   "))

    assert provider.calls == []


def test_missing_route_is_reported() -> None:
    provider = FakeProvider()
    controller = make_controller(provider, {})

    with pytest.raises(RouteNotConfiguredError):
        controller.generate(GenerationRequest("Explain a concept"))

    assert provider.calls == []


def test_provider_connection_failure_is_normalized() -> None:
    provider = UnavailableProvider()
    config = ModelConfig(provider="fake", model="general-model")
    controller = make_controller(provider, {TaskType.GENERAL: config})

    with pytest.raises(ProviderUnavailableError):
        controller.generate(GenerationRequest("Explain a concept"))


def test_provider_timeout_is_normalized() -> None:
    provider = TimeoutProvider()
    config = ModelConfig(provider="fake", model="general-model")
    controller = make_controller(provider, {TaskType.GENERAL: config})

    with pytest.raises(ProviderTimeoutError):
        controller.generate(GenerationRequest("Explain a concept"))