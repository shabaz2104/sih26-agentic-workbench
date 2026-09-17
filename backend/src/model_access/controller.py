"""Application-facing Model Access Controller."""

from .classifier import TaskClassifier
from .contracts import GenerationRequest, GenerationResponse, ModelConfig, TaskType
from .errors import (
    InvalidRequestError,
    ModelAccessError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from .routing import ModelRouter
from .providers.base import ModelProvider


class ModelAccessController:
    """Coordinate validation, classification, routing, and generation."""

    def __init__(
        self,
        classifier: TaskClassifier,
        router: ModelRouter,
        provider: ModelProvider,
    ) -> None:
        self._classifier = classifier
        self._router = router
        self._provider = provider

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text through the configured route and provider."""
        self._validate_request(request)
        task_type = request.task_type or self._classifier.classify(request.prompt)
        model_config = self._router.route(task_type)

        try:
            text = self._provider.generate(request, model_config)
        except ModelAccessError:
            raise
        except TimeoutError as error:
            raise ProviderTimeoutError("The model provider timed out") from error
        except ConnectionError as error:
            raise ProviderUnavailableError("The model provider is unavailable") from error
        except Exception as error:
            raise ProviderResponseError("The model provider failed") from error

        if not isinstance(text, str):
            raise ProviderResponseError("The model provider returned non-text output")

        return GenerationResponse(
            text=text,
            task_type=task_type,
            provider=model_config.provider,
            model=model_config.model,
        )

    @staticmethod
    def _validate_request(request: GenerationRequest) -> None:
        if not request.prompt.strip():
            raise InvalidRequestError("The prompt must not be empty")
        if request.temperature is not None and request.temperature < 0:
            raise InvalidRequestError("Temperature must not be negative")
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise InvalidRequestError("max_tokens must be greater than zero")