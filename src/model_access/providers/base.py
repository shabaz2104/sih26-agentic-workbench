"""Provider interface used by the controller."""

from typing import Protocol

from ..contracts import GenerationRequest, ModelConfig


class ModelProvider(Protocol):
    """Abstraction over a model server or local inference implementation."""

    def generate(self, request: GenerationRequest, config: ModelConfig) -> str:
        """Generate text for a request using the supplied model configuration."""