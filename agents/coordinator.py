from typing import Any, Dict, Optional
from tools.generate import generate_exercise
from tools.validate import validate_exercise


def run_coordinator(
    learning_goal: str,
    target_grade: int = 1,
    difficulty: str = "medium",
    exercise_type: str = "phonics",
    extra_constraints: str = "",
    max_attempts: int = 3,
    min_confidence: float = 0.7,
) -> Dict[str, Any]:
    """
    Simple multi-agent coordinator.

    Pattern:
    1. Coordinator receives the high-level goal
    2. Delegates generation to the Generator specialist
    3. Explicitly passes the generated exercise to the Validator specialist
    4. Decides whether to retry (with feedback) or finish / escalate
    """

    feedback: Optional[str] = None
    last_exercise = None
    history = []  # for observability

    for attempt in range(1, max_attempts + 1):
        print(f"\n=== Coordinator – Attempt {attempt}/{max_attempts} ===")

        # --------------------------------------------------
        # 1. Coordinator → Generator (explicit context)
        # --------------------------------------------------
        print("  [Coordinator] Delegating to Generator...")

        gen_input = {
            "learning_goal": learning_goal,
            "target_grade": target_grade,
            "difficulty": difficulty,
            "exercise_type": exercise_type,
            "extra_constraints": extra_constraints,
        }

        if feedback:
            # Explicitly pass previous failure context to the Generator
            gen_input["extra_constraints"] = (
                f"{extra_constraints}\n\n"
                f"IMPORTANT – Previous attempt was rejected. Fix these problems:\n{feedback}"
            ).strip()

        gen_result = generate_exercise(gen_input)

        if gen_result.get("isError") or gen_result.get("status") != "success":
            print("  [Generator] Failed:", gen_result.get("message"))
            feedback = gen_result.get("message", "Generation failed")
            history.append({"attempt": attempt, "stage": "generate", "result": "failed"})
            continue

        exercise = gen_result["exercise"]
        last_exercise = exercise
        print(f"  [Generator] Produced: {exercise.get('title')}")

        # --------------------------------------------------
        # 2. Coordinator → Validator (explicit context passing)
        # --------------------------------------------------
        print("  [Coordinator] Passing exercise to Validator...")

        # Key exam concept: we explicitly pass the complete exercise.
        # The Validator does not inherit any previous conversation.
        val_result = validate_exercise({
            "exercise": exercise,
            "strict_mode": True,
        })

        if val_result.get("isError"):
            print("  [Validator] Failed:", val_result.get("message"))
            feedback = val_result.get("message", "Validation failed")
            history.append({"attempt": attempt, "stage": "validate", "result": "failed"})
            continue

        is_acceptable = val_result.get("is_acceptable", False)
        confidence = val_result.get("exercise", {}).get("confidence", 0.0)
        issues = val_result.get("issues", [])
        suggestions = val_result.get("suggestions", [])
        summary = val_result.get("summary", "")

        print(f"  [Validator] Acceptable: {is_acceptable} | Confidence: {confidence:.2f}")
        if issues:
            print(f"  [Validator] Issues: {issues}")

        history.append({
            "attempt": attempt,
            "stage": "validate",
            "is_acceptable": is_acceptable,
            "confidence": confidence,
            "issues": issues,
        })

        # --------------------------------------------------
        # 3. Coordinator decides what to do next
        # --------------------------------------------------
        if is_acceptable and confidence >= min_confidence:
            print("  [Coordinator] Decision: Accept exercise")
            return {
                "status": "success",
                "attempts": attempt,
                "exercise": val_result["exercise"],
                "validation_summary": summary,
                "history": history,
            }

        # Not good enough → prepare explicit feedback for the next Generator call
        feedback_parts = []
        if issues:
            feedback_parts.append("Issues:\n- " + "\n- ".join(issues))
        if suggestions:
            feedback_parts.append("Suggestions:\n- " + "\n- ".join(suggestions))
        if summary:
            feedback_parts.append(f"Summary: {summary}")

        feedback = "\n\n".join(feedback_parts) or "Exercise was not acceptable."
        print("  [Coordinator] Decision: Retry with feedback")

    # --------------------------------------------------
    # All attempts exhausted → escalate to human
    # --------------------------------------------------
    print("\n  [Coordinator] Decision: Escalate to human review")

    if last_exercise:
        last_exercise["needs_human_review"] = True
        last_exercise["validation_notes"] = (
            f"Failed after {max_attempts} attempts. Last feedback: {feedback}"
        )

    return {
        "status": "needs_human_review",
        "attempts": max_attempts,
        "exercise": last_exercise,
        "last_feedback": feedback,
        "history": history,
    }