"""Configuration-driven task-to-model routing."""

from collections.abc import Mapping

from .contracts import ModelConfig, TaskType
from .errors import RouteNotConfiguredError


class ModelRouter:
    """Return the configured model route for a task category."""

    def __init__(self, routes: Mapping[TaskType, ModelConfig]) -> None:
        self._routes = dict(routes)

    def route(self, task_type: TaskType) -> ModelConfig:
        """Look up a model configuration or report a missing route."""
        try:
            return self._routes[task_type]
        except KeyError as error:
            raise RouteNotConfiguredError(
                f"No model route configured for task type: {task_type.value}"
            ) from error