import json
from typing import Any, Dict

import anthropic
from pydantic import ValidationError

from schemas.exercise import Exercise, EXERCISE_JSON_SCHEMA
from tools.definitions import make_error


client = anthropic.Anthropic()


def generate_exercise(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real implementation of the generate_exercise tool.
    Forces structured output using tool_use + the Exercise JSON Schema.
    """

    learning_goal = tool_input.get("learning_goal", "")
    target_grade = tool_input.get("target_grade", 1)
    difficulty = tool_input.get("difficulty", "medium")
    exercise_type = tool_input.get("exercise_type", "phonics")
    extra_constraints = tool_input.get("extra_constraints", "")

    # We ask Claude to call a special "submit_exercise" tool whose input_schema
    # is exactly our Exercise schema. This is the cleanest way to get reliable
    # structured output (Domain 4 best practice).
    submit_tool = {
        "name": "submit_exercise",
        "description": "Submit the final educational exercise. You must call this tool with a complete, valid exercise.",
        "input_schema": EXERCISE_JSON_SCHEMA,
    }

    system = f"""
You are an expert educational content designer for young children (Project Gem).
Create one high-quality exercise that matches the request.

Rules:
- Keep language simple, encouraging, and age-appropriate for grade {target_grade}.
- The correct answer must be unambiguous.
- If the type supports multiple choice, provide 3 good distractors.
- Fill learning_objective clearly.
- Do not invent scary or inappropriate themes.
- You MUST call the submit_exercise tool with the complete exercise. Do not reply with free text.
""".strip()

    user_content = f"""
Create an exercise with these requirements:

- Learning goal: {learning_goal}
- Target grade: {target_grade}
- Difficulty: {difficulty}
- Type: {exercise_type}
- Extra constraints: {extra_constraints or "None"}
""".strip()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            tools=[submit_tool],
            tool_choice={"type": "tool", "name": "submit_exercise"},  # force the structured tool
            messages=[{"role": "user", "content": user_content}],
        )

        # Extract the tool call
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_exercise":
                raw = block.input
                try:
                    exercise = Exercise.model_validate(raw)
                    # Start with a reasonable confidence; validation step can adjust it
                    if exercise.confidence is None:
                        exercise.confidence = 0.75
                    return {
                        "status": "success",
                        "exercise": exercise.model_dump(mode="json"),
                    }
                except ValidationError as e:
                    return make_error(
                        message="Generated exercise failed schema validation",
                        error_category="validation",
                        is_retryable=True,
                        details={"pydantic_errors": e.errors(), "raw": raw},
                    )

        return make_error(
            message="Model did not call submit_exercise",
            error_category="validation",
            is_retryable=True,
        )

    except Exception as e:
        return make_error(
            message=f"Generation failed: {str(e)}",
            error_category="transient",
            is_retryable=True,
        )