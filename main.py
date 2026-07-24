from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise ValueError("API key not found in environment variables.")

from core.loop import run_agentic_loop

if __name__ == "__main__":
    user_request = (
        "Create a medium-difficulty phonics exercise for grade 1 "
        "focused on the short 'a' sound in CVC words. "
        "Make it multiple choice with 3 distractors."
    )

    print("Running agentic loop...\n")
    result = run_agentic_loop(user_request)

    print("\n===== RESULT =====")
    print("Status:", result["status"])
    print("Iterations:", result.get("iterations"))
    if "final_text" in result:
        print("\nFinal text:\n", result["final_text"])