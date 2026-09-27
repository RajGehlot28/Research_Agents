import os
import re
import sys
import time
import warnings
from dotenv import load_dotenv

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Suppress AFC warnings
class _FilteredStream:
    def __init__(self, target):
        self._target = target
    def write(self, s):
        if "automatic function calling" in s or "AFC" in s:
            return
        if self._target:
            self._target.write(s)
    def flush(self):
        if self._target:
            self._target.flush()
    def __getattr__(self, name):
        return getattr(self._target, name)

if sys.stderr and not isinstance(sys.stderr, _FilteredStream):
    sys.stderr = _FilteredStream(sys.stderr)
if sys.stdout and not isinstance(sys.stdout, _FilteredStream):
    sys.stdout = _FilteredStream(sys.stdout)

warnings.filterwarnings("ignore")

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def get_llm(role: str = "default", temperature: float = 0.2):
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Use role-specific key if available, otherwise fall back to GEMINI_API_KEY
    role_key = f"{role.upper()}_API_KEY" if role else ""
    api_key = os.getenv(role_key, "").strip() if role_key else ""
    if not api_key:
        api_key = GEMINI_API_KEY

    if not api_key:
        raise ValueError(f"No API key found. Set {role_key} or GEMINI_API_KEY in .env")

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
        max_retries=1,
    )


def invoke_with_retry(llm, messages, max_attempts: int = 4):
    last_err = None

    for attempt in range(max_attempts):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_err = e
            msg = str(e)

            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "rate_limit" in msg.lower():
                delay_match = (
                    re.search(r"retry in\s+([0-9\.]+)\s*s", msg, re.IGNORECASE)
                    or re.search(r"retryDelay['\":\s]+([0-9\.]+)\s*s", msg, re.IGNORECASE)
                    or re.search(r"try again in\s+([0-9\.]+)\s*s", msg, re.IGNORECASE)
                )
                wait_sec = min(float(delay_match.group(1)) + 1.5, 60.0) if delay_match else min(3.0 * (attempt + 1), 20.0)
                print(f"[LLM Rate Limit] Waiting {wait_sec:.1f}s (attempt {attempt + 1}/{max_attempts})...", flush=True)
                time.sleep(wait_sec)

            elif "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg or "Server disconnected" in msg:
                wait = 2.0 * (attempt + 1)
                print(f"[LLM] Server unavailable. Retrying in {wait:.1f}s...", flush=True)
                time.sleep(wait)

            else:
                wait = 2.0 * (attempt + 1)
                print(f"[LLM] Retrying after: {msg[:80]}... in {wait}s", flush=True)
                time.sleep(wait)

    raise RuntimeError(f"LLM call failed after {max_attempts} attempts: {last_err}")


def extract_text(response) -> str:
    content = response.content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return str(content).strip()
