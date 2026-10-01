import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # if role specific api key is not available it will be used

def get_llm(role: str, temperature: float = 0.2):
    # Use role-specific key if available, otherwise fall back to GEMINI_API_KEY
    role_key = f"{role.upper()}_API_KEY"
    api_key = os.getenv(role_key)

    if not api_key:
        raise ValueError(f"No API key found. Set {role_key} or GEMINI_API_KEY in .env")

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
        max_retries=1,
    )


def invoke_with_retry(llm, messages):
    max_attempts = 5
    last_err = None
    for attempt in range(max_attempts):
        try:
            return llm.invoke(messages)
        except Exception as e:
                last_err = e
                # if llm api call failed then retrying after 2 sec
                wait_sec = 2.0
                print(f"LLM Server unavailable. Retrying in {wait_sec}s...")
                time.sleep(wait_sec)

    raise RuntimeError(f"LLM call failed after {max_attempts} attempts: {last_err}")


def extract_text(response) -> str:
    content = response.content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return content
