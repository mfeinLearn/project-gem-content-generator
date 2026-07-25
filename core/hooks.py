from typing import Any, Dict
from datetime import datetime, timezone


def post_tool_use_hook(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    PostToolUse-style interception (CCA-F Domain 1).

    Runs after every tool call, before the result is fed back
    into the agent / coordinator decision logic.
    """
    # Observability
    status = tool_result.get("status")
    is_error = tool_result.get("isError", False)
    print(f"  [PostToolUse] tool={tool_name} status={status} isError={is_error}")

    # Shallow copy so we don't mutate the original unexpectedly
    result = dict(tool_result)

    # Normalization example: ensure confidence exists on exercises
    exercise = result.get("exercise")
    if isinstance(exercise, dict):
        exercise.setdefault("confidence", 0.5)
        result["exercise"] = exercise

    # Lightweight audit trail
    result["_hook"] = {
        "tool": tool_name,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    return result