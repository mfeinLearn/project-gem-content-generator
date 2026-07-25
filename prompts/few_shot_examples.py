FEW_SHOT_EXAMPLES = [
    {
        "learning_goal": "short 'a' sound in CVC words",
        "target_grade": 1,
        "difficulty": "medium",
        "exercise_type": "phonics",
        "example": {
            "type": "phonics",
            "title": "Short 'a' Animal Match",
            "prompt": "Which word has the same middle sound as 'cat'?",
            "correct_answer": "bat",
            "difficulty": "medium",
            "learning_objective": "Identify the short 'a' vowel sound in simple CVC words.",
            "target_grade": 1,
            "distractors": ["hen", "pig", "fox"],
            "hints": [
                "Say 'cat' slowly and listen to the middle sound.",
                "The short 'a' sounds like the 'a' in 'apple'.",
                "Find the word that rhymes with 'cat'."
            ],
            "success_criteria": "Child selects 'bat'.",
            "explanation": "'Bat' has the short 'a' sound, just like 'cat'. The others have different vowel sounds.",
            "tags": ["short-a", "CVC", "phonics"]
        }
    },
    {
        "learning_goal": "two-digit addition without carrying",
        "target_grade": 2,
        "difficulty": "easy",
        "exercise_type": "math",
        "example": {
            "type": "math",
            "title": "Add the Tens and Ones",
            "prompt": "What is 23 + 14?",
            "correct_answer": "37",
            "difficulty": "easy",
            "learning_objective": "Add two-digit numbers without regrouping.",
            "target_grade": 2,
            "distractors": ["27", "33", "47"],
            "hints": [
                "Add the ones place first: 3 + 4.",
                "Then add the tens place: 2 + 1.",
                "Put the two parts together."
            ],
            "success_criteria": "Child answers 37.",
            "explanation": "3 + 4 = 7 ones, 2 + 1 = 3 tens, so the answer is 37.",
            "tags": ["addition", "two-digit", "no-regrouping"]
        }
    },
    {
        "learning_goal": "write a simple sentence about an animal",
        "target_grade": 1,
        "difficulty": "medium",
        "exercise_type": "writing",
        "example": {
            "type": "writing",
            "title": "Animal Sentence",
            "prompt": "Write one complete sentence about a dog. Start with a capital letter and end with a period.",
            "correct_answer": "The dog runs fast.",
            "difficulty": "medium",
            "learning_objective": "Write a complete simple sentence with correct capitalization and punctuation.",
            "target_grade": 1,
            "distractors": None,
            "hints": [
                "A sentence needs a who/what and an action.",
                "Start with a capital letter.",
                "End with a period."
            ],
            "success_criteria": "Child produces a complete sentence about a dog with capital letter and period.",
            "explanation": "A complete sentence names who or what and tells what they do. It starts with a capital and ends with a period.",
            "tags": ["writing", "sentences", "capitalization"]
        }
    },
]


def format_few_shot_for_prompt(max_examples: int = 2) -> str:
    """Return a compact string of few-shot examples for injection into a system or user prompt."""
    lines = ["Here are examples of high-quality exercises:"]
    for i, item in enumerate(FEW_SHOT_EXAMPLES[:max_examples], 1):
        ex = item["example"]
        lines.append(f"\nExample {i} ({item['exercise_type']}, grade {item['target_grade']}):")
        lines.append(f"  Title: {ex['title']}")
        lines.append(f"  Prompt: {ex['prompt']}")
        lines.append(f"  Correct answer: {ex['correct_answer']}")
        lines.append(f"  Learning objective: {ex['learning_objective']}")
        if ex.get("distractors"):
            lines.append(f"  Distractors: {', '.join(ex['distractors'])}")
    return "\n".join(lines)