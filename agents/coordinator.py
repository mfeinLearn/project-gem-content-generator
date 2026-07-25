from typing import Any, Dict, Optional, List
from tools.generate import generate_exercise
from tools.validate import validate_exercise
from core.persist import save_exercise
from core.guards import enforce_confidence_threshold
from core.hooks import post_tool_use_hook


def plan_parallel_tasks(
    learning_goal: str,
    extra_constraints: str = "",
) -> List[Dict[str, str]]:
    """
    Exam pattern: coordinator declares multiple specialist tasks that could
    be emitted as parallel Task tool calls in a single assistant turn.

    Each task has an isolated prompt (explicit context, no shared history).
    """
    return [
        {
            "subagent": "generator",
            "prompt": (
                f"Generate one educational exercise.\n"
                f"Learning goal: {learning_goal}\n"
                f"Constraints: {extra_constraints or 'None'}"
            ),
        },
        {
            "subagent": "style_critic",
            "prompt": (
                "You only review age-appropriateness and tone for young children. "
                "Do not regenerate content. Return brief findings only."
            ),
        },
    ]


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
    2. Optionally plans parallel specialist tasks (Task-tool pattern)
    3. Delegates generation to the Generator specialist
    4. Explicitly passes the generated exercise to the Validator specialist
    5. Applies PostToolUse hooks + programmatic enforcement
    6. Decides whether to retry (with feedback) or finish / escalate
    """

    feedback: Optional[str] = None
    last_exercise = None
    history: List[Dict[str, Any]] = []

    # Demonstrate parallel Task-style planning (Domain 1 stretch)
    parallel_plan = plan_parallel_tasks(learning_goal, extra_constraints)
    print("  [Coordinator] Parallel task plan:")
    for t in parallel_plan:
        print(f"    - {t['subagent']}: {t['prompt'][:80]}...")

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
        gen_result = post_tool_use_hook("generate_exercise", gen_input, gen_result)

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
        val_input = {
            "exercise": exercise,
            "strict_mode": True,
        }
        val_result = validate_exercise(val_input)
        val_result = post_tool_use_hook("validate_exercise", val_input, val_result)

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
        # 3. Coordinator + programmatic enforcement gate
        # --------------------------------------------------
        if is_acceptable:
            allowed, reason = enforce_confidence_threshold(
                val_result["exercise"],
                min_confidence=min_confidence,
            )

            if allowed:
                print(f"  [Coordinator] Decision: Accept exercise ({reason})")

                saved_path = save_exercise(
                    val_result["exercise"],
                    meta={
                        "attempts": attempt,
                        "learning_goal": learning_goal,
                        "validation_summary": summary,
                        "enforcement": reason,
                    },
                )
                print(f"  [Coordinator] Saved to {saved_path}")

                return {
                    "status": "success",
                    "attempts": attempt,
                    "exercise": val_result["exercise"],
                    "validation_summary": summary,
                    "history": history,
                    "saved_path": str(saved_path),
                }
            else:
                print(f"  [Enforcement] Blocked: {reason}")
                # Treat as failure so we retry with feedback
                feedback = f"Programmatic guard rejected the exercise: {reason}"
                history.append({
                    "attempt": attempt,
                    "stage": "enforcement",
                    "result": "blocked",
                    "reason": reason,
                })
                continue

        # Not acceptable → build feedback for next attempt
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