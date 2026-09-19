import httpx
from bs4 import BeautifulSoup

def web_fetch(url: str, max_chars: int = 4000) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    timeout = httpx.Timeout(8.0, connect=4.0)
    try:
        with httpx.Client(verify=False, timeout=timeout) as client:
            resp = client.get(url, headers=headers, follow_redirects=True)

        if resp.status_code != 200:
            return f"Error: Failed to fetch page. HTTP status code {resp.status_code}"

        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip noisy elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            tag.extract()

        text = " ".join(soup.stripped_strings)
        if len(text) > max_chars:
            text = text[:max_chars] + "... [content truncated]"
        return text
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
