---
name: add-exercise-type
description: Scaffold a new exercise type (e.g. geometry, writing) including schema updates and tool considerations.
---

When the user wants to support a new exercise type:

1. Update `schemas/exercise.py` (add to the `ExerciseType` enum if needed).
2. Consider whether the existing `generate_exercise` / `validate_exercise` tools need new fields or prompts.
3. Add 1–2 few-shot style examples for the new type.
4. Keep changes minimal and backward-compatible.