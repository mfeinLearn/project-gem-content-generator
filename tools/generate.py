import json
from typing import Any, Dict

import anthropic
from pydantic import ValidationError

from schemas.exercise import Exercise, EXERCISE_JSON_SCHEMA
from tools.definitions import make_error
from prompts.few_shot_examples import format_few_shot_for_prompt

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

    # Forced structured output tool (Domain 4)
    submit_tool = {
        "name": "submit_exercise",
        "description": "Submit the final educational exercise. You must call this tool with a complete, valid exercise.",
        "input_schema": EXERCISE_JSON_SCHEMA,
    }

    few_shot = format_few_shot_for_prompt(max_examples=2)

    # Critical rules placed at TOP and BOTTOM to mitigate lost-in-the-middle
    critical_rules = f"""
CRITICAL RULES (must follow):
1. Age-appropriate for grade {target_grade} only.
2. Correct answer must be unambiguous.
3. If multiple choice, provide exactly 3 plausible distractors.
4. Do not give away the answer in the prompt or early hints.
5. You MUST call the submit_exercise tool — no free-text final answer.
""".strip()

    system = f"""
You are an expert educational content designer for young children (Project Gem).

{critical_rules}

Create one high-quality exercise that matches the request.

{few_shot}

Additional guidance:
- Keep language simple and encouraging.
- Fill learning_objective clearly.
- No scary or inappropriate themes.
- Follow the style and quality of the examples above.

{critical_rules}
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
            model="claude-sonnet-5",
            max_tokens=2048,
            system=system,
            tools=[submit_tool],
            tool_choice={"type": "tool", "name": "submit_exercise"},  # forced tool selection
            messages=[{"role": "user", "content": user_content}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_exercise":
                raw = block.input
                try:
                    exercise = Exercise.model_validate(raw)
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