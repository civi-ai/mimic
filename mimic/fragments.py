import re
import json


def parse_subtasks(raw: str) -> list[str]:
    """Parse Claude's subtask response, tolerating markdown code fences."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def build_merge_prompt(task: str, fragment_results: list[str]) -> str:
    n = len(fragment_results)
    fragments_text = "\n".join(
        f"Fragment {i + 1}: {r}" for i, r in enumerate(fragment_results)
    )
    return (
        f"Merge these {n} research fragments into one unified response.\n\n"
        f"Original task: {task}\n\n"
        f"{fragments_text}\n\n"
        f"Produce one clean unified response."
    )
