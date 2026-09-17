"""Deterministic task classification for the initial MVP."""

from typing import Protocol

from .contracts import TaskType


class TaskClassifier(Protocol):
    """Interface allowing the classifier to be replaced later."""

    def classify(self, prompt: str) -> TaskType:
        """Return the task category for a prompt."""


class KeywordTaskClassifier:
    """Classify prompts using a small, deterministic coding keyword set."""

    _coding_keywords = frozenset(
        {
            "algorithm",
            "api",
            "bug",
            "class",
            "code",
            "coding",
            "debug",
            "function",
            "implement",
            "javascript",
            "parse",
            "program",
            "python",
            "sql",
        }
    )

    def classify(self, prompt: str) -> TaskType:
        """Use whole-word keyword matches; unmatched prompts are general."""
        words = set(prompt.lower().replace("_", " ").split())
        if words & self._coding_keywords:
            return TaskType.CODING
        return TaskType.GENERAL