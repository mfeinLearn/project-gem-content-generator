from typing import Any, Dict

import anthropic
from pydantic import ValidationError

from schemas.exercise import Exercise
from tools.definitions import make_error


client = anthropic.Anthropic()


def validate_exercise(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real implementation of the validate_exercise tool.
    Returns a structured assessment + updated confidence / needs_human_review.
    """

    raw_exercise = tool_input.get("exercise")
    strict_mode = tool_input.get("strict_mode", False)

    if not raw_exercise:
        return make_error(
            message="No exercise provided",
            error_category="validation",
            is_retryable=False,
        )

    # First, make sure it still matches our schema
    try:
        exercise = Exercise.model_validate(raw_exercise)
    except ValidationError as e:
        return make_error(
            message="Exercise does not match the required schema",
            error_category="validation",
            is_retryable=True,
            details={"pydantic_errors": e.errors()},
        )

    # Ask Claude to critique it against clear criteria
    system = """
You are a strict but fair educational content reviewer for a children's learning game (ages ~5–12).
Evaluate the exercise on these criteria:

1. Age-appropriateness for the stated target_grade
2. Clarity of the prompt (will a child understand what to do?)
3. Correctness of the correct_answer
4. Quality of distractors (if present) — are they plausible but clearly wrong?
5. Educational value of the learning_objective
6. Overall tone (encouraging, never scary or inappropriate)

Respond with a JSON object only, using this shape:
{
  "is_acceptable": true/false,
  "confidence": 0.0-1.0,
  "needs_human_review": true/false,
  "issues": ["list of specific problems"],
  "suggestions": ["list of concrete improvements"],
  "summary": "one sentence overall assessment"
}
""".strip()

    user_content = f"""
Strict mode: {strict_mode}

Exercise to review:
{exercise.model_dump_json(indent=2)}
""".strip()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )

        # Very simple extraction (in production you would also force a tool here)
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        # Try to parse the JSON the model returned
        import json
        import re

        # Extract the first JSON object we find
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return make_error(
                message="Validator did not return valid JSON",
                error_category="validation",
                is_retryable=True,
                details={"raw_response": text},
            )

        review = json.loads(match.group(0))

        # Update the exercise with validation results
        exercise.confidence = float(review.get("confidence", 0.5))
        exercise.needs_human_review = bool(review.get("needs_human_review", False))
        exercise.validation_notes = review.get("summary", "")

        if not review.get("is_acceptable", False):
            exercise.needs_human_review = True

        return {
            "status": "success",
            "is_acceptable": review.get("is_acceptable", False),
            "exercise": exercise.model_dump(mode="json"),
            "issues": review.get("issues", []),
            "suggestions": review.get("suggestions", []),
            "summary": review.get("summary", ""),
        }

    except Exception as e:
        return make_error(
            message=f"Validation failed: {str(e)}",
            error_category="transient",
            is_retryable=True,
        )