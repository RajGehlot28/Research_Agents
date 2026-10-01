import httpx
from bs4 import BeautifulSoup

def web_fetch(url: str, max_chars: int = 4000) -> str:
    # adding this header will ensure that web servers will treat the request like a regular human visit -> prevent from anti-bot blocking
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = httpx.get(url, headers=headers, timeout=8.0, follow_redirects=True, verify=False)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)
        return text[:max_chars]
    except Exception as e:
        print(f"[WARN] Fetch error for '{url}': {e}")
        return ""
