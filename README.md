# Project Gem Content Generator

AI-powered educational content generator and validator for [Project Gem](https://github.com/mfeinLearn/Project-Gem) — an educational game focused on literacy, writing, and arithmetic for children.

This project generates structured, age-appropriate exercises (phonics, math, writing, geometry, etc.) and validates them for quality, correctness, and suitability before they are used in the game.

## Goals

1. **Practical** — Produce real, usable educational content for the unfinished Project Gem web version.
2. **Learning** — Deliberately practice the skills tested on the **Claude Certified Architect – Foundations (CCA-F)** exam, especially:
   - Structured output with JSON Schema + tool use
   - Tool design and clear tool descriptions
   - Agentic loops (`stop_reason` handling)
   - Validation → retry loops
   - Confidence scoring and human escalation patterns
   - (Later) Multi-agent orchestration with explicit context passing

## Current Status

- Core Exercise schema defined (Pydantic + JSON Schema)
- Tool definitions created (`generate_exercise`, `validate_exercise`)
- Single-agent agentic loop implemented
- System prompt with explicit escalation criteria
- Next: real generation + validation logic, then multi-agent expansion

## Tech Stack

- Python
- Official Anthropic Python SDK
- Pydantic for structured data

## Project Structure

```text
├── schemas/          # Exercise data model
├── tools/            # Tool definitions and helpers
├── prompts/          # System prompts
├── core/             # Agentic loop and shared utilities
├── agents/           # (Future) Multi-agent components
└── examples/         # Usage examples
```

## Getting Started

```bash
# Clone the repo
git clone https://github.com/mfeinLearn/project-gem-content-generator.git
cd project-gem-content-generator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
python main.py
```

## License

TBD
