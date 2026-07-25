"""
Message Batches API pattern (CCA-F Domain 4 – stretch).

When to use Batches:
- Many independent jobs (e.g. generate 20 phonics + 20 math exercises overnight)
- You can tolerate minutes/hours of latency
- You do NOT need interactive multi-turn tool loops per item

When NOT to use Batches:
- Single interactive agent loops
- Tight validation-retry that needs immediate feedback
- Anything that depends on shared conversation state across items

Each batch request is independent — no shared history between items.
"""

from typing import Any, Dict, List


def build_batch_requests(
    learning_goals: List[str],
    target_grade: int = 1,
    model: str = "claude-3-5-sonnet-20241022",
) -> List[Dict[str, Any]]:
    """
    Build a list of independent batch requests.

    Real usage (Anthropic Batches API):
        batch = client.messages.batches.create(requests=build_batch_requests([...]))
        # later:
        # client.messages.batches.retrieve(batch.id)
        # client.messages.batches.results(batch.id)
    """
    requests = []
    for i, goal in enumerate(learning_goals):
        requests.append(
            {
                "custom_id": f"goal-{i}-{goal[:20].replace(' ', '-')}",
                "params": {
                    "model": model,
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"Generate one grade {target_grade} educational exercise "
                                f"for this learning goal: {goal}. "
                                f"Return a short JSON object with title, prompt, "
                                f"correct_answer, and distractors."
                            ),
                        }
                    ],
                },
            }
        )
    return requests


# Example (not executed automatically)
EXAMPLE_GOALS = [
    "short 'a' sound in CVC words",
    "two-digit addition without carrying",
    "write a simple sentence about an animal",
    "recognize a circle vs a square",
    "sight word: the",
]


if __name__ == "__main__":
    reqs = build_batch_requests(EXAMPLE_GOALS)
    print(f"Built {len(reqs)} independent batch requests")
    print("First custom_id:", reqs[0]["custom_id"])
    print("\nRemember: Batches are for throughput, not for interactive agent loops.")
