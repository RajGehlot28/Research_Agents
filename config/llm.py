import os
import sys
import re
import time
import warnings
from dotenv import load_dotenv

# Configure pycache prefix to root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("PYTHONPYCACHEPREFIX", os.path.join(BASE_DIR, "__pycache__"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Suppress AFC warning on stderr
class _FilteredStderr:
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

if sys.stderr and not isinstance(sys.stderr, _FilteredStderr):
    sys.stderr = _FilteredStderr(sys.stderr)

warnings.filterwarnings("ignore")
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Active Gemini models supporting generateContent for automatic quota fallback
GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
]

_key_index = 0
_model_index = 0

def get_api_keys() -> list[str]:
    raw = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    return [k.strip() for k in re.split(r"[,;\n]", raw) if k.strip()]

def get_llm(model: str = None, temperature: float = 0.2, key_index: int = None, model_index: int = None):
    keys = get_api_keys()
    if not keys:
        raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in environment or .env file.")

    idx = key_index if key_index is not None else _key_index
    active_key = keys[idx % len(keys)]

    if model:
        target_model = model
    elif "GEMINI_MODEL" in os.environ and model_index is None:
        target_model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    else:
        m_idx = model_index if model_index is not None else _model_index
        target_model = GEMINI_MODELS[m_idx % len(GEMINI_MODELS)]

    return ChatGoogleGenerativeAI(
        model=target_model,
        google_api_key=active_key,
        temperature=temperature,
        convert_system_message_to_human=True,
        max_retries=1,
    )

def invoke_with_retry(llm, messages, max_attempts: int = 6):
    global _key_index, _model_index
    keys = get_api_keys()
    last_err = None
    current_llm = llm

    for attempt in range(max_attempts):
        try:
            return current_llm.invoke(messages)
        except Exception as e:
            last_err = e
            msg = str(e)

            # Check for 429 quota exhaustion or rate limit
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                # Extract suggested retry delay from error message if present
                delay_match = re.search(r"retry in\s+([0-9\.]+)\s*s", msg, re.IGNORECASE)
                if not delay_match:
                    delay_match = re.search(r"retryDelay['\":\s]+([0-9\.]+)\s*s", msg, re.IGNORECASE)

                if delay_match:
                    wait_sec = min(float(delay_match.group(1)) + 1.0, 35.0)
                else:
                    wait_sec = min(4.0 * (attempt + 1), 25.0)

                # If multiple keys are available, try the next key first
                if len(keys) > 1 and (_key_index + 1) % len(keys) != 0:
                    _key_index = (_key_index + 1) % len(keys)
                    print(f"[LLM Info] Rotating to next Gemini API key (Key #{_key_index + 1}) due to rate limit...")
                    current_llm = get_llm(key_index=_key_index)
                    time.sleep(1)
                    continue

                # If all keys on the current model reached quota, rotate to next Gemini model
                _model_index = (_model_index + 1) % len(GEMINI_MODELS)
                next_model = GEMINI_MODELS[_model_index]
                print(f"[LLM Info] Quota reached on active model. Rotating to Gemini '{next_model}' (waiting {wait_sec:.1f}s)...")
                time.sleep(wait_sec)
                current_llm = get_llm(model=next_model, key_index=_key_index)
                continue

            elif "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg or "Server disconnected" in msg:
                # Rotate to another Gemini model to avoid overloaded endpoints
                _model_index = (_model_index + 1) % len(GEMINI_MODELS)
                next_model = GEMINI_MODELS[_model_index]
                print(f"[LLM Info] Model overloaded or unavailable. Rotating to Gemini '{next_model}'...")
                time.sleep(2)
                current_llm = get_llm(model=next_model, key_index=_key_index)
                continue

            elif "NOT_FOUND" in msg or "404" in msg:
                _model_index = (_model_index + 1) % len(GEMINI_MODELS)
                next_model = GEMINI_MODELS[_model_index]
                print(f"[LLM Warning] Model unavailable. Switching to Gemini '{next_model}'...")
                current_llm = get_llm(model=next_model, key_index=_key_index)
                time.sleep(1)
                continue

            else:
                wait = 2 * (attempt + 1)
                print(f"[LLM Warning] Retrying after issue: {msg[:70]}... in {wait}s")
                time.sleep(wait)

    raise RuntimeError(f"Gemini LLM call failed after {max_attempts} attempts: {last_err}")

def extract_text(response) -> str:
    content = response.content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return str(content).strip()

