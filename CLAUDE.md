# Project: Game Content Generator with Validation (for Project Gem)

## Purpose

We are building an AI-powered **Game Content Generator with Validation** that produces educational exercises for **Project Gem**, an unfinished educational game focused on literacy, writing, and arithmetic for children.

This project has two goals:

1. **Practical value**: Generate real, usable educational content (phonics, math, writing prompts, geometry, etc.) that can be fed into the incomplete Project Gem web game.
2. **Exam preparation**: Deliberately practice the skills tested on the **Claude Certified Architect – Foundations (CCAR-F / CCA-F)** exam.

## Background – Project Gem

- Original: Global Learning XPRIZE finalist educational game (Android / libGDX, real-time multiplayer).
- Current effort: Web version (`project-gem-web` – still incomplete).
- Focus areas: literacy (phonics, reading, writing), arithmetic, simple geometry.
- Target users: children (early elementary grades).
- Content must be age-appropriate, educationally sound, balanced, and correctly structured for the game.

## What We Are Building

An agent (starting as a single agent, later expandable to multi-agent) that:

1. Accepts a learning goal + target grade/age + difficulty.
2. Generates educational exercises (phonics, math, writing, geometry, etc.).
3. Validates them for:
   - Educational quality
   - Age-appropriateness
   - Balance / fairness
   - Correctness
4. Outputs clean, structured JSON that the game can consume.
5. Automatically retries when validation fails.
6. Escalates low-confidence or ambiguous cases to a human with a structured handoff.

### Core Design Principles (aligned with CCA-F)

- Prefer **tool_use + JSON Schema** for structured output (not free-form JSON).
- Use clear, non-overlapping tool descriptions.
- Implement structured error responses (`errorCategory`, `isRetryable`, human-readable messages).
- Explicit validation → retry-with-error-feedback loops.
- Field-level confidence scoring + human escalation path.
- Later: coordinator + specialist subagents with **explicit context passing** (no automatic inheritance).

## Tech Decisions (Agreed)

- **Language**: Python
- **SDK**: Official `anthropic` Python package (we will structure the code to teach Agent SDK patterns: agentic loop with `stop_reason`, tool definitions, explicit context passing, etc.)
- **API key**: User already has an Anthropic API key
- **No mock mode needed** for now

## Project Structure (Planned)

```text
project-gem-content-generator/
├── CLAUDE.md                 ← this file
├── README.md
├── requirements.txt
├── .env.example
├── schemas/
│   └── exercise.py           # Pydantic models + JSON Schema
├── tools/
│   ├── generate.py
│   ├── validate.py
│   ├── balance.py
│   └── format_for_game.py
├── agents/
│   ├── single_agent.py       # Start here
│   ├── coordinator.py        # Later (multi-agent)
│   ├── generator_agent.py
│   └── validator_agent.py
├── prompts/
│   ├── system_single.py
│   ├── system_coordinator.py
│   └── few_shot_examples.py
├── core/
│   ├── loop.py               # Agentic loop
│   ├── errors.py
│   └── confidence.py
└── examples/
    └── sample_generation.py
```

## Exam Domain Coverage (Primary Focus of This Project)

| Domain | Weight | Coverage by this project | Notes |
|--------|--------|---------------------------|-------|
| 1. Agentic Architecture & Orchestration | 27% | Moderate → Strong (once multi-agent) | Agentic loop, later coordinator + subagents, explicit context passing, iterative refinement |
| 2. Tool Design & MCP Integration | 18% | Strong | Clear tool descriptions, structured errors, tool_choice, possible MCP later |
| 3. Claude Code Configuration & Workflows | 20% | Minimal | Will be covered in a follow-up exercise on the real `project-gem-web` repo |
| 4. Prompt Engineering & Structured Output | 20% | Excellent | JSON Schema + tool_use, few-shot, validation-retry, nullable fields |
| 5. Context Management & Reliability | 15% | Very Strong | Escalation, confidence scoring, fact persistence, structured errors |

## Current Status (as of 2026-07-24)

- Project concept and exam mapping agreed.
- Excel tracker created: `CCA-F_Game_Content_Generator_Tracker.xlsx`
- Tech choices confirmed (Python + official anthropic SDK).
- Ready to begin implementation starting with:
  1. Exercise JSON Schema (`schemas/exercise.py`)
  2. Tool definitions + descriptions + error shapes
  3. Single-agent system prompt + agentic loop
  4. Validation-retry + confidence + escalation
  5. (Stretch) Multi-agent expansion

## Key Checklist Items This Project Intentionally Hits

**High priority for this project:**
- 4.3 / 4.4 – Structured output via tool_use + JSON Schema (required/optional/nullable, enums)
- 4.1 / 4.2 – Explicit criteria + few-shot examples
- 4.6 / 4.7 – Validation → retry-with-error-feedback
- 2.1–2.6 – Tool design, descriptions, structured errors, tool_choice, scoping
- 5.4 / 5.8 – Explicit escalation criteria + field-level confidence + human review routing
- 1.1 / 1.2 – Correct agentic loop with stop_reason + tool result handling
- 1.7 / 1.9 – Iterative refinement + structured handoff summaries
- 1.3–1.6 (later) – Multi-agent coordinator pattern with explicit context passing

**Intentionally deferred (Domain 3):**
- CLAUDE.md hierarchy, `.claude/rules/`, slash commands, skills, plan mode, CI integration  
  → These will be done as a separate short exercise on the real `project-gem-web` codebase after this generator is working.

## Important Constraints & Principles

- Content must be suitable for children (age-appropriate language and topics).
- Prefer deterministic structured output over free-form text.
- Prefer programmatic validation + retry over hoping the model gets it right on the first try.
- Prefer explicit escalation criteria over vague “be careful” instructions.
- Keep tools focused and non-overlapping.
- When we move to multi-agent, always pass complete relevant findings in the prompt (subagents do not inherit context automatically).

## Next Immediate Step

Create the core **Exercise JSON Schema** (Pydantic models) in `schemas/exercise.py`.  
This is the foundation for structured output (checklist items 4.3 and 4.4).

---

*This file exists so that any future Claude session or Claude Code instance has the full context of what we are building and why.*
