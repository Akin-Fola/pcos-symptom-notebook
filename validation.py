from pydantic import BaseModel, field_validator, ValidationError as PydanticValidationError

MIN_LENGTH = 50
SOFT_MAX_LENGTH = 1000
HARD_MAX_LENGTH = 2000


class ValidationError(Exception):
    """Raised when a narrative fails validation, with a user-safe message."""
    pass

class NarrativeInput(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if value is None:
            raise ValueError("Narrative text is required.")

        stripped = value.strip()

        if len(stripped) == 0:
            raise ValueError("Narrative cannot be empty.")

        if len(stripped) < MIN_LENGTH:
            raise ValueError(
                f"Narrative too short (min {MIN_LENGTH} characters, got {len(stripped)})."
            )

        if len(stripped) > HARD_MAX_LENGTH:
            raise ValueError(
                f"Narrative too long (max {HARD_MAX_LENGTH} characters, got {len(stripped)})."
            )

        return stripped

def validate_narrative(text: str) -> dict:
    """
    Validate a raw narrative string.
    Returns {"validated_text": str, "over_recommended_length": bool}
    Raises ValidationError with a user-safe message on failure.
    """
    try:
        parsed = NarrativeInput(text=text)
    except PydanticValidationError as exc:
        first_error = exc.errors()[0]
        message = first_error["msg"].removeprefix("Value error, ")
        raise ValidationError(message) from exc

    return {
        "validated_text": parsed.text,
        "over_recommended_length": len(parsed.text) > SOFT_MAX_LENGTH,
    }
