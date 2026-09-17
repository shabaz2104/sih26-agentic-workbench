"""Exceptions exposed by the model access module."""


class ModelAccessError(Exception):
    """Base exception for model access failures."""


class InvalidRequestError(ModelAccessError):
    """Raised when a generation request is invalid."""


class RouteNotConfiguredError(ModelAccessError):
    """Raised when no model configuration exists for a task type."""


class ProviderUnavailableError(ModelAccessError):
    """Raised when a provider cannot be reached."""


class ProviderTimeoutError(ModelAccessError):
    """Raised when a provider takes too long to respond."""


class ProviderResponseError(ModelAccessError):
    """Raised when a provider returns an invalid response."""