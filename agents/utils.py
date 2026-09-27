import json
import re

def parse_json_response(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: regex search for outer JSON object or array
        match = re.search(r"(\{|\[).*(\}|\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

def make_links_clickable(text: str) -> str:
    if not text:
        return ""

    def replace_url(match):
        url = match.group(1)
        suffix = ""
        while url and url[-1] in ".,;:!?":
            suffix = url[-1] + suffix
            url = url[:-1]
        return f"[{url}]({url}){suffix}"

    pattern = r"(?<!\]\()(?<!\[)(https?://[^\s\)\],]+)"
    return re.sub(pattern, replace_url, text)
