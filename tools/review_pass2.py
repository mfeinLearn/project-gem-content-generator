from typing import Any, Dict, List
import anthropic
from pydantic import BaseModel, Field, ValidationError

from tools.definitions import make_error


client = anthropic.Anthropic()


class Pass2Result(BaseModel):
    """Focused second-pass review."""
    passes: bool = Field(..., description="Whether this pass accepts the exercise")
    confidence: float = Field(..., ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    focus_summary: str = Field(..., description="One-sentence finding for this pass")


PASS2_SCHEMA = Pass2Result.model_json_schema()


def review_pass2(exercise: Dict[str, Any]) -> Dict[str, Any]:
    """
    Second review pass (multi-pass architecture).

    Focus only on:
    1. Do the hints give away the answer too early?
    2. Does the exercise actually test the stated learning objective?
    3. Are distractors testing the skill (not just random wrong answers)?
    """

    submit_tool = {
        "name": "submit_pass2_review",
        "description": "Submit the focused second-pass review. You must call this tool.",
        "input_schema": PASS2_SCHEMA,
    }

    system = """
You are a strict second-pass reviewer for children's educational exercises.

ONLY evaluate these three things:
1. Hint leakage — do any hints effectively reveal the correct answer?
2. Skill alignment — does the task actually test the learning_objective?
3. Distractor quality — do wrong options target common confusions for this skill?

Do NOT re-check basic grammar, tone, or schema. That was Pass 1.

You MUST call submit_pass2_review. No free text.
""".strip()

    user_content = f"""
Exercise to review (Pass 2 — focused):

{exercise}
""".strip()

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=800,
            system=system,
            tools=[submit_tool],
            tool_choice={"type": "tool", "name": "submit_pass2_review"},
            messages=[{"role": "user", "content": user_content}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_pass2_review":
                try:
                    review = Pass2Result.model_validate(block.input)
                except ValidationError as e:
                    return make_error(
                        message="Pass 2 result failed schema validation",
                        error_category="validation",
                        is_retryable=True,
                        details={"pydantic_errors": e.errors()},
                    )

                return {
                    "status": "success",
                    "passes": review.passes,
                    "confidence": review.confidence,
                    "issues": review.issues,
                    "suggestions": review.suggestions,
                    "focus_summary": review.focus_summary,
                }

        return make_error(
            message="Pass 2 model did not call submit_pass2_review",
            error_category="validation",
            is_retryable=True,
        )

    except Exception as e:
        return make_error(
            message=f"Pass 2 review failed: {str(e)}",
            error_category="transient",
            is_retryable=True,
        )