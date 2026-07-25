"""
Minimal MCP server for Project Gem Content Generator.

Exposes:
- Resource: learning-goals://catalog
- Tool: get_learning_goal
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("project-gem-content")

# Simple in-memory catalog (could later load from a file or DB)
LEARNING_GOALS = {
    "phonics-short-a": {
        "id": "phonics-short-a",
        "type": "phonics",
        "grade": 1,
        "description": "Short 'a' sound in CVC words",
        "example_prompt": "Which word has the same middle sound as 'cat'?",
    },
    "math-add-two-digit": {
        "id": "math-add-two-digit",
        "type": "math",
        "grade": 2,
        "description": "Two-digit addition without regrouping",
        "example_prompt": "What is 23 + 14?",
    },
    "writing-simple-sentence": {
        "id": "writing-simple-sentence",
        "type": "writing",
        "grade": 1,
        "description": "Write a complete simple sentence with capital and period",
        "example_prompt": "Write one complete sentence about a dog.",
    },
}


@mcp.resource("learning-goals://catalog")
def learning_goals_catalog() -> str:
    """Return the full catalog of available learning goals."""
    import json
    return json.dumps(list(LEARNING_GOALS.values()), indent=2)


@mcp.tool()
def get_learning_goal(goal_id: str) -> str:
    """
    Fetch a single learning goal by id.
    Valid ids: phonics-short-a, math-add-two-digit, writing-simple-sentence
    """
    import json
    goal = LEARNING_GOALS.get(goal_id)
    if not goal:
        return json.dumps({"error": f"Unknown goal_id: {goal_id}"})
    return json.dumps(goal, indent=2)


if __name__ == "__main__":
    mcp.run()