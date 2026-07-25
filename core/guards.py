from typing import Any, Dict, Tuple


def enforce_confidence_threshold(
    exercise: Dict[str, Any],
    min_confidence: float = 0.7,
) -> Tuple[bool, str]:
    """
    Programmatic enforcement gate (Domain 1.8).

    Returns (allowed, reason).
    Even if the model says the exercise is acceptable, we can still block it.
    """
    confidence = exercise.get("confidence")

    if confidence is None:
        return False, "Missing confidence score – cannot accept without a score."

    if confidence < min_confidence:
        return (
            False,
            f"Confidence {confidence:.2f} is below required threshold {min_confidence:.2f}.",
        )

    return True, "Passed confidence enforcement gate."