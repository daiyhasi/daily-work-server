import json
import re
from typing import Any


FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def parse_json_object(text: str) -> Any:
    cleaned = text.strip()
    fenced = FENCED_JSON_RE.search(cleaned)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])

