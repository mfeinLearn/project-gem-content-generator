---
paths:
  - "schemas/**"
  - "tools/**"
---

# Schema & Tool Rules

- Any new structured output must go through a Pydantic model and expose `.model_json_schema()`.
- Tool descriptions must clearly state what the tool is for **and** what it is not for.
- Prefer forced `tool_choice` when the model must produce a specific schema.
- Keep generation and validation tools strictly separated.