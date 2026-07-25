import json
from typing import Any, Dict, Optional

from tools.generate import generate_exercise
from tools.validate import validate_exercise
from tools.definitions import make_error


def run_generate_with_retry(
    learning_goal: str,
    target_grade: int = 1,
    difficulty: str = "medium",
    exercise_type: str = "phonics",
    extra_constraints: str = "",
    max_attempts: int = 3,
    min_confidence: float = 0.7,
) -> Dict[str, Any]:
    """
    Generate → Validate → Retry loop.

    This implements the classic validation-retry pattern tested in CCA-F Domain 4.
    """

    feedback = None
    last_result = None

    for attempt in range(1, max_attempts + 1):
        print(f"\n=== Attempt {attempt}/{max_attempts} ===")

        # Build the generation input
        gen_input = {
            "learning_goal": learning_goal,
            "target_grade": target_grade,
            "difficulty": difficulty,
            "exercise_type": exercise_type,
            "extra_constraints": extra_constraints,
        }

        # If we have feedback from a previous failed attempt, add it
        if feedback:
            gen_input["extra_constraints"] = (
                f"{extra_constraints}\n\n"
                f"IMPORTANT - Previous attempt had these problems. Fix them:\n{feedback}"
            ).strip()

        # 1. Generate
        print("  → Generating...")
        gen_result = generate_exercise(gen_input)

        if gen_result.get("isError") or gen_result.get("status") != "success":
            print("  ✗ Generation failed:", gen_result.get("message", gen_result))
            last_result = gen_result
            feedback = gen_result.get("message", "Generation failed")
            continue

        exercise = gen_result["exercise"]
        print(f"  ✓ Generated: {exercise.get('title', 'Untitled')}")

        # 2. Validate
        print("  → Validating...")
        val_result = validate_exercise({
            "exercise": exercise,
            "strict_mode": True,
        })

        if val_result.get("isError"):
            print("  ✗ Validation call failed:", val_result.get("message"))
            last_result = val_result
            feedback = val_result.get("message", "Validation failed")
            continue

        is_acceptable = val_result.get("is_acceptable", False)
        confidence = val_result.get("exercise", {}).get("confidence", 0.0)
        issues = val_result.get("issues", [])
        suggestions = val_result.get("suggestions", [])
        summary = val_result.get("summary", "")

        print(f"  → Acceptable: {is_acceptable} | Confidence: {confidence:.2f}")
        if issues:
            print(f"  → Issues: {issues}")

        # 3. Decision
        if is_acceptable and confidence >= min_confidence:
            print("  ✓ Success!")
            return {
                "status": "success",
                "attempts": attempt,
                "exercise": val_result["exercise"],
                "validation_summary": summary,
            }

        # Not good enough — prepare feedback for next attempt
        feedback_parts = []
        if issues:
            feedback_parts.append("Issues found:\n- " + "\n- ".join(issues))
        if suggestions:
            feedback_parts.append("Suggestions:\n- " + "\n- ".join(suggestions))
        if summary:
            feedback_parts.append(f"Summary: {summary}")

        feedback = "\n\n".join(feedback_parts) or "Exercise was not acceptable. Please improve it."
        last_result = val_result

        print("  ✗ Not good enough — will retry with feedback")

    # All attempts exhausted
    print("\n✗ Max attempts reached. Marking for human review.")
    final_exercise = last_result.get("exercise") if last_result else None

    if final_exercise:
        final_exercise["needs_human_review"] = True
        final_exercise["validation_notes"] = (
            f"Failed after {max_attempts} attempts. Last feedback: {feedback}"
        )

    return {
        "status": "needs_human_review",
        "attempts": max_attempts,
        "exercise": final_exercise,
        "last_feedback": feedback,
    }