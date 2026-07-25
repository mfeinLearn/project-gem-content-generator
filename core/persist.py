import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_exercise(exercise: Dict[str, Any], meta: Dict[str, Any] | None = None) -> Path:
    """
    Save an accepted exercise to output/ as a JSON file.
    Returns the path of the saved file.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    title_slug = (
        exercise.get("title", "exercise")
        .lower()
        .replace(" ", "-")
        .replace("'", "")[:40]
    )
    filename = f"{timestamp}_{title_slug}.json"
    path = OUTPUT_DIR / filename

    record = {
        "saved_at": timestamp,
        "exercise": exercise,
        "meta": meta or {},
    }

    path.write_text(json.dumps(record, indent=2))
    return path