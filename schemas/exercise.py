from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ExerciseType(str, Enum):
    PHONICS = "phonics"
    MATH = "math"
    WRITING = "writing"
    GEOMETRY = "geometry"
    OTHER = "other"


class Difficulty(str, Enum):
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class Exercise(BaseModel):
    """
    Core schema for a Project Gem educational exercise.
    Designed for reliable structured output via tool_use + JSON Schema.
    """

    # --- Required core fields ---
    type: ExerciseType = Field(
        ...,
        description="Primary category of the exercise"
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Short, child-friendly title"
    )
    prompt: str = Field(
        ...,
        min_length=10,
        description="The main question or instruction shown to the child"
    )
    correct_answer: str = Field(
        ...,
        description="The expected correct answer (string so it works across types)"
    )
    difficulty: Difficulty = Field(
        ...,
        description="Target difficulty level"
    )
    learning_objective: str = Field(
        ...,
        description="Clear statement of what the child should learn or practice"
    )
    target_grade: int = Field(
        ...,
        ge=0,
        le=6,
        description="Approximate target grade level (0 = kindergarten/pre-K)"
    )

    # --- Optional / nullable fields (important for preventing hallucination) ---
    distractors: Optional[List[str]] = Field(
        default=None,
        description="Wrong answers for multiple-choice style exercises. Null if not applicable."
    )
    hints: Optional[List[str]] = Field(
        default=None,
        description="Progressive hints the game can reveal. Null if none."
    )
    success_criteria: Optional[str] = Field(
        default=None,
        description="How the game should decide the child succeeded"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Simple explanation shown after answering (age-appropriate)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags e.g. ['short-a', 'addition', 'carrying']"
    )

    # --- Metadata used by our validation & confidence system ---
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model's self-assessed confidence (0–1). Set by generation or validation step."
    )
    needs_human_review: bool = Field(
        default=False,
        description="True when confidence is low or validation found issues that need a human"
    )
    validation_notes: Optional[str] = Field(
        default=None,
        description="Any notes from the validation step (null if clean)"
    )

    # --- Extensibility ---
    extra: Optional[dict] = Field(
        default=None,
        description="Escape hatch for type-specific data that doesn't fit the common fields"
    )

    @field_validator("distractors")
    @classmethod
    def check_distractors(cls, v, info):
        if v is not None and len(v) > 6:
            raise ValueError("Too many distractors (max 6)")
        return v


# Convenience: the JSON Schema that we will feed to tool_use
EXERCISE_JSON_SCHEMA = Exercise.model_json_schema()


if __name__ == "__main__":
    # Quick sanity check
    print("Schema generated successfully.")
    print("Required fields:", Exercise.model_json_schema()["required"])