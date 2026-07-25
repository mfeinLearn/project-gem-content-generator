from typing import Any, Dict
from datetime import datetime, timezone


# Fields safe to keep on an exercise when passing results around
_EXERCISE_KEEP = {
    "type", "title", "prompt", "correct_answer", "difficulty",
    "learning_objective", "target_grade", "distractors", "hints",
    "success_criteria", "explanation", "tags", "confidence",
    "needs_human_review", "validation_notes",
}


def _trim_exercise(exercise: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(exercise, dict):
        return exercise
    trimmed = {k: exercise[k] for k in _EXERCISE_KEEP if k in exercise}
    # Avoid carrying huge optional blobs
    if trimmed.get("explanation") and len(str(trimmed["explanation"])) > 400:
        trimmed["explanation"] = str(trimmed["explanation"])[:400] + "…"
    return trimmed


def post_tool_use_hook(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    PostToolUse interception + verbose output trimming (Domain 5).
    """
    status = tool_result.get("status")
    is_error = tool_result.get("isError", False)
    print(f"  [PostToolUse] tool={tool_name} status={status} isError={is_error}")

    result = dict(tool_result)

    # Trim exercise payloads
    if isinstance(result.get("exercise"), dict):
        result["exercise"] = _trim_exercise(result["exercise"])

    # Drop bulky debug-only fields if present
    for bulky in ("raw_response", "pydantic_errors", "details"):
        if bulky in result and not result.get("isError"):
            # Keep details only on errors; drop on success paths
            if bulky != "details":
                result.pop(bulky, None)
        elif bulky in result and bulky == "details" and not result.get("isError"):
            result.pop(bulky, None)

    # Cap long issue/suggestion lists
    for list_key in ("issues", "suggestions"):
        if isinstance(result.get(list_key), list) and len(result[list_key]) > 5:
            result[list_key] = result[list_key][:5] + ["…(trimmed)"]

    result["_hook"] = {
        "tool": tool_name,
        "ts": datetime.now(timezone.utc).isoformat(),
        "trimmed": True,
    }
    return result