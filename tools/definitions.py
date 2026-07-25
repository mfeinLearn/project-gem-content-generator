from typing import Any, Dict, List
from schemas.exercise import Exercise, ExerciseType, Difficulty


# Canonical error categories used in this project
# - transient: retry may help (network, rate limit)
# - validation: bad input / schema mismatch (retry with fix)
# - business: valid request but domain rule failed (e.g. unknown id)
# - permission: auth / access denied (do not treat as empty success)
ERROR_CATEGORIES = ("transient", "validation", "business", "permission")


# ------------------------------------------------------------------
# Structured error shape we will use everywhere (exam-aligned)
# ------------------------------------------------------------------
def make_error(
    message: str,
    error_category: str,          # "transient" | "validation" | "business" | "permission"
    is_retryable: bool = False,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Standard structured error response.
    Matches the patterns tested in Domain 2 (isError, errorCategory, isRetryable).
    """
    if error_category not in ERROR_CATEGORIES:
        # Fail closed to a safe non-retryable validation error if mis-categorized
        error_category = "validation"
        is_retryable = False
        details = {
            **(details or {}),
            "_note": f"Invalid error_category coerced to 'validation'. Allowed: {ERROR_CATEGORIES}",
        }

    return {
        "isError": True,
        "errorCategory": error_category,
        "isRetryable": is_retryable,
        "message": message,
        "details": details or {},
    }


def simple_error(
    message: str,
    error_category: str = "validation",
    is_retryable: bool = False,
) -> Dict[str, Any]:
    """
    Convenience helper for the common case where all we have is a message.

    Delegates to make_error so the error shape stays defined in exactly one place.
    Defaults to a non-retryable validation error, which is the safe choice for an
    unclassified failure: it will not trigger a retry loop.
    """
    return make_error(
        message=message,
        error_category=error_category,
        is_retryable=is_retryable,
    )


# ------------------------------------------------------------------
# Tool 1: generate_exercise
# ------------------------------------------------------------------
GENERATE_EXERCISE_TOOL = {
    "name": "generate_exercise",
    "description": (
        "Generate a new educational exercise for Project Gem (children's literacy, "
        "math, writing, or geometry game). "
        "Use this tool when you need to create a fresh exercise from a learning goal. "
        "Do NOT use this tool to validate or critique an existing exercise — use validate_exercise for that. "
        "Always produce content that is age-appropriate, encouraging, and educationally sound."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "learning_goal": {
                "type": "string",
                "description": "What the child should practice, e.g. 'short a sound in CVC words' or 'two-digit addition with carrying'"
            },
            "target_grade": {
                "type": "integer",
                "minimum": 0,
                "maximum": 6,
                "description": "Target grade level (0 = kindergarten/pre-K)"
            },
            "difficulty": {
                "type": "string",
                "enum": ["very_easy", "easy", "medium", "hard", "very_hard"],
                "description": "Desired difficulty"
            },
            "exercise_type": {
                "type": "string",
                "enum": ["phonics", "math", "writing", "geometry", "other"],
                "description": "Primary category of the exercise"
            },
            "extra_constraints": {
                "type": "string",
                "description": "Optional extra instructions, e.g. 'use only animals as themes' or 'multiple choice with 3 distractors'"
            }
        },
        "required": ["learning_goal", "target_grade", "difficulty", "exercise_type"]
    }
}


# ------------------------------------------------------------------
# Tool 2: validate_exercise
# ------------------------------------------------------------------
VALIDATE_EXERCISE_TOOL = {
    "name": "validate_exercise",
    "description": (
        "Validate an existing educational exercise for Project Gem. "
        "Checks: educational quality, age-appropriateness for the target grade, "
        "correctness of the answer, balance of distractors (if any), clarity of the prompt, "
        "and overall suitability for children. "
        "Use this tool AFTER generating an exercise or when reviewing one. "
        "Do NOT use this tool to create new exercises — use generate_exercise for creation. "
        "Returns a structured assessment including confidence and whether human review is needed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "exercise": {
                "type": "object",
                "description": "The full exercise object to validate (must match the Exercise schema)"
            },
            "strict_mode": {
                "type": "boolean",
                "description": "If true, apply stricter criteria suitable for production content. Default false."
            }
        },
        "required": ["exercise"]
    }
}


# List of tools we will pass to the Anthropic client
TOOLS = [GENERATE_EXERCISE_TOOL, VALIDATE_EXERCISE_TOOL]


# ------------------------------------------------------------------
# Helper: convert our Pydantic Exercise into a plain dict for tool results
# ------------------------------------------------------------------
def exercise_to_dict(exercise: Exercise) -> Dict[str, Any]:
    return exercise.model_dump(mode="json")