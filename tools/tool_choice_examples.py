"""
tool_choice patterns (CCA-F Domain 2 / 4)

forced  -> must call this exact tool (best for JSON Schema / submit_* tools)
any     -> must call some tool, model chooses which
auto    -> optional tool use (default)
"""

# 1) Forced — what generate.py / review_pass2.py already do
FORCED_SUBMIT_EXERCISE = {"type": "tool", "name": "submit_exercise"}
FORCED_SUBMIT_VALIDATION = {"type": "tool", "name": "submit_validation"}
FORCED_PASS2 = {"type": "tool", "name": "submit_pass2_review"}

# 2) Any — require a tool call, but allow the model to choose among tools
TOOL_CHOICE_ANY = {"type": "any"}

# 3) Auto — model decides whether to call a tool at all
TOOL_CHOICE_AUTO = "auto"  # or {"type": "auto"}


def choose_tool_choice(*, require_structured_submit: bool, multi_tool_router: bool = False):
    """
    Tiny decision helper for exam-style reasoning.
    """
    if require_structured_submit:
        return "forced"  # pair with {"type":"tool","name": specific_submit_tool}
    if multi_tool_router:
        return "any"
    return "auto"