from typing import Any, Dict, List, Optional
from tools.definitions import make_error


# Simulated catalog (same ideas as the MCP stub)
LEARNING_GOALS = {
    "phonics-short-a": {
        "id": "phonics-short-a",
        "type": "phonics",
        "grade": 1,
        "description": "Short 'a' sound in CVC words",
    },
    "math-add-two-digit": {
        "id": "math-add-two-digit",
        "type": "math",
        "grade": 2,
        "description": "Two-digit addition without regrouping",
    },
}


def list_learning_goals(
    *,
    access_token: Optional[str] = "ok",
) -> Dict[str, Any]:
    """
    Return catalog entries.

    Distinguishes:
    - permission failure (bad/missing token)
    - valid empty list (filter matched nothing)
    - normal success with data
    """
    # Access failure — NOT an empty success
    if access_token != "ok":
        return make_error(
            message="Not authorized to read learning goals catalog",
            error_category="permission",
            is_retryable=False,
            details={"reason": "invalid_or_missing_token"},
        )

    goals: List[Dict[str, Any]] = list(LEARNING_GOALS.values())
    return {
        "status": "success",
        "goals": goals,          # may be empty list in other filters
        "count": len(goals),
    }


def get_learning_goal(
    goal_id: str,
    *,
    access_token: Optional[str] = "ok",
) -> Dict[str, Any]:
    """
    Fetch one goal by id.

    - permission → errorCategory permission
    - unknown id → business (valid call, no such entity)
    - found → success with object
    """
    if access_token != "ok":
        return make_error(
            message="Not authorized to read learning goal",
            error_category="permission",
            is_retryable=False,
        )

    goal = LEARNING_GOALS.get(goal_id)
    if goal is None:
        # Important: this is NOT permission and NOT a bare empty success
        return make_error(
            message=f"No learning goal with id '{goal_id}'",
            error_category="business",
            is_retryable=False,
            details={"goal_id": goal_id},
        )

    return {
        "status": "success",
        "goal": goal,
    }


def search_learning_goals(
    query: str,
    *,
    access_token: Optional[str] = "ok",
) -> Dict[str, Any]:
    """
    Search catalog.

    Valid empty result: status=success, goals=[], count=0
    (caller must not treat this like an access failure)
    """
    if access_token != "ok":
        return make_error(
            message="Not authorized to search learning goals",
            error_category="permission",
            is_retryable=False,
        )

    q = (query or "").strip().lower()
    matches = [
        g for g in LEARNING_GOALS.values()
        if q in g["id"] or q in g["description"].lower() or q in g["type"]
    ]

    # Valid empty — success with zero hits
    return {
        "status": "success",
        "goals": matches,
        "count": len(matches),
        "query": query,
    }