"""Typed data contracts used by the model access boundary."""

from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    """Task categories supported by the first controller version."""

    CODING = "coding"
    GENERAL = "general"


@dataclass(frozen=True)
class GenerationRequest:
    """Input accepted by the model access controller."""

    prompt: str
    task_type: TaskType | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class GenerationResponse:
    """Provider-independent response returned by the controller."""

    text: str
    task_type: TaskType
    provider: str
    model: str


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for one routed model."""

    provider: str
    model: str
    endpoint: str = ""
    timeout_seconds: float = 60.0