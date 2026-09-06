import pytest
from validation import validate_narrative, ValidationError, MIN_LENGTH, HARD_MAX_LENGTH


def test_too_short():
    with pytest.raises(ValidationError):
        validate_narrative("short")


def test_empty():
    with pytest.raises(ValidationError):
        validate_narrative("")


def test_too_long():
    with pytest.raises(ValidationError):
        validate_narrative("a" * (HARD_MAX_LENGTH + 1))


def test_valid():
    text = "I have irregular periods and weight gain that started about two years ago."
    assert len(text) >= MIN_LENGTH
    result = validate_narrative(text)
    assert result["validated_text"] == text
    assert result["over_recommended_length"] is False
