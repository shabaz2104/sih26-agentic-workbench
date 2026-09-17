import pytest

from model_access.contracts import ModelConfig, TaskType
from model_access.errors import RouteNotConfiguredError
from model_access.routing import ModelRouter


def test_router_returns_configuration_for_task_type() -> None:
    coding_config = ModelConfig(provider="fake", model="coding-model")
    router = ModelRouter({TaskType.CODING: coding_config})

    assert router.route(TaskType.CODING) == coding_config


def test_router_raises_for_missing_route() -> None:
    router = ModelRouter({})

    with pytest.raises(RouteNotConfiguredError):
        router.route(TaskType.GENERAL)