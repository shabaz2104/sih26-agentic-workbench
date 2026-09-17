from backend.src.model_access.classifier import KeywordTaskClassifier
from backend.src.model_access.contracts import TaskType


def test_coding_prompt_is_classified_as_coding() -> None:
    classifier = KeywordTaskClassifier()

    assert classifier.classify("Write a Python function to parse a CSV file") == TaskType.CODING


def test_explanatory_prompt_is_classified_as_general() -> None:
    classifier = KeywordTaskClassifier()

    assert classifier.classify("Explain what retrieval augmented generation is") == TaskType.GENERAL