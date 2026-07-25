from dotenv import load_dotenv
load_dotenv()  # Must be first — before any module that creates an Anthropic client

import os
import json
from core.retry import run_generate_with_retry

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("API key not found. Make sure you have a .env file with ANTHROPIC_API_KEY=...")


if __name__ == "__main__":
    result = run_generate_with_retry(
        learning_goal="short 'a' sound in CVC words",
        target_grade=1,
        difficulty="medium",
        exercise_type="phonics",
        extra_constraints="Make it multiple choice with 3 distractors. Use simple animal themes.",
        max_attempts=3,
        min_confidence=0.7,
    )

    print("\n" + "=" * 50)
    print("FINAL RESULT")
    print("=" * 50)
    print("Status:", result["status"])
    print("Attempts:", result["attempts"])

    if result.get("exercise"):
        print("\nExercise:")
        print(json.dumps(result["exercise"], indent=2))