---
paths:
  - "**/*.py"
---

# Python Style Rules for this project

- Use type hints on all function signatures.
- Prefer Pydantic models for structured data.
- Keep tool functions pure where possible (input → output, minimal side effects).
- Always use the structured error helper (`make_error`) for tool failures.
- Do not hardcode API keys; always load from environment via dotenv.