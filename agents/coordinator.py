from typing import Any, Dict, Optional, List
from tools.generate import generate_exercise
from tools.validate import validate_exercise
from tools.review_pass2 import review_pass2
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
    Multi-agent coordinator with multi-pass review.

    Flow:
    1. Plan parallel tasks (Task-tool pattern)
    2. Generate
    3. Pass 1 validate (general quality)
    4. Pass 2 focused critic (hints / skill alignment / distractors)
    5. Programmatic enforcement gate
    6. Retry with feedback or escalate
    """

    feedback: Optional[str] = None
    last_exercise = None
    history: List[Dict[str, Any]] = []

    parallel_plan = plan_parallel_tasks(learning_goal, extra_constraints)
    print("  [Coordinator] Parallel task plan:")
    for t in parallel_plan:
        print(f"    - {t['subagent']}: {t['prompt'][:80]}...")

    for attempt in range(1, max_attempts + 1):
        print(f"\n=== Coordinator – Attempt {attempt}/{max_attempts} ===")

        # --------------------------------------------------
        # 1. Generator
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
        # 2. Pass 1 — general validation
        # --------------------------------------------------
        print("  [Coordinator] Passing exercise to Validator (Pass 1)...")

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

        print(f"  [Pass1] Acceptable: {is_acceptable} | Confidence: {confidence:.2f}")
        if issues:
            print(f"  [Pass1] Issues: {issues}")

        history.append({
            "attempt": attempt,
            "stage": "validate",
            "is_acceptable": is_acceptable,
            "confidence": confidence,
            "issues": issues,
        })

        if not is_acceptable:
            feedback_parts = []
            if issues:
                feedback_parts.append("Pass 1 issues:\n- " + "\n- ".join(issues))
            if suggestions:
                feedback_parts.append("Pass 1 suggestions:\n- " + "\n- ".join(suggestions))
            if summary:
                feedback_parts.append(f"Pass 1 summary: {summary}")
            feedback = "\n\n".join(feedback_parts) or "Failed Pass 1 validation."
            print("  [Coordinator] Decision: Retry (failed Pass 1)")
            continue

        # --------------------------------------------------
        # 2b. Pass 2 — focused critic (multi-pass review)
        # --------------------------------------------------
        print("  [Coordinator] Running Pass 2 (focused critic)...")
        pass2 = review_pass2(exercise)
        pass2 = post_tool_use_hook("review_pass2", {"exercise": exercise}, pass2)

        if pass2.get("isError"):
            print("  [Pass2] Failed:", pass2.get("message"))
            feedback = pass2.get("message", "Pass 2 failed")
            history.append({"attempt": attempt, "stage": "pass2", "result": "failed"})
            continue

        print(f"  [Pass2] Passes: {pass2.get('passes')} | Confidence: {pass2.get('confidence', 0):.2f}")
        if pass2.get("issues"):
            print(f"  [Pass2] Issues: {pass2.get('issues')}")

        history.append({
            "attempt": attempt,
            "stage": "pass2",
            "passes": pass2.get("passes"),
            "confidence": pass2.get("confidence"),
            "issues": pass2.get("issues", []),
        })

        if not pass2.get("passes", False):
            feedback_parts = []
            if pass2.get("issues"):
                feedback_parts.append("Pass 2 issues:\n- " + "\n- ".join(pass2["issues"]))
            if pass2.get("suggestions"):
                feedback_parts.append("Pass 2 suggestions:\n- " + "\n- ".join(pass2["suggestions"]))
            if pass2.get("focus_summary"):
                feedback_parts.append(f"Pass 2 summary: {pass2['focus_summary']}")
            feedback = "\n\n".join(feedback_parts) or "Failed focused second-pass review."
            print("  [Coordinator] Decision: Retry (failed Pass 2)")
            continue

        # Combine confidences (take the more conservative score)
        p2_conf = float(pass2.get("confidence", 1.0))
        if val_result.get("exercise") is not None:
            p1_conf = float(val_result["exercise"].get("confidence") or 0.0)
            combined = min(p1_conf, p2_conf)
            val_result["exercise"]["confidence"] = combined
            confidence = combined
            print(f"  [Coordinator] Combined confidence: {confidence:.2f}")

        # --------------------------------------------------
        # 3. Programmatic enforcement gate
        # --------------------------------------------------
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
                    "pass2_summary": pass2.get("focus_summary"),
                    "enforcement": reason,
                },
            )
            print(f"  [Coordinator] Saved to {saved_path}")

            return {
                "status": "success",
                "attempts": attempt,
                "exercise": val_result["exercise"],
                "validation_summary": summary,
                "pass2_summary": pass2.get("focus_summary"),
                "history": history,
                "saved_path": str(saved_path),
            }

        print(f"  [Enforcement] Blocked: {reason}")
        feedback = f"Programmatic guard rejected the exercise: {reason}"
        history.append({
            "attempt": attempt,
            "stage": "enforcement",
            "result": "blocked",
            "reason": reason,
        })
        continue

    # --------------------------------------------------
    # Escalate
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