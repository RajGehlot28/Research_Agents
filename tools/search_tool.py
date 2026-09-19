import os
import httpx
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse

MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

import re

def simplify_query(query: str) -> str:
    stop_words = {"of", "and", "the", "for", "in", "with", "a", "an", "to", "on", "at", "by", "from", "about"}
    words = [w for w in re.findall(r"\b[a-zA-Z0-9_\.-]+\b", query) if w.lower() not in stop_words]
    return " ".join(words[:6])

def _execute_search(q: str, limit: int, headers: dict, timeout: httpx.Timeout) -> list[dict]:
    results = []
    try:
        with httpx.Client(verify=False, timeout=timeout) as client:
            resp = client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": q},
                headers=headers,
                follow_redirects=True
            )
            if resp.status_code != 200:
                resp = client.post(
                    "https://lite.duckduckgo.com/lite/",
                    data={"q": q},
                    headers=headers,
                    follow_redirects=True
                )

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".result"):
                title_elem = item.select_one(".result__title a")
                snippet_elem = item.select_one(".result__snippet")

                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    raw_href = title_elem.get("href", "")

                    if "uddg=" in raw_href:
                        parsed = parse_qs(urlparse(raw_href).query)
                        url = parsed.get("uddg", [raw_href])[0]
                    else:
                        url = raw_href

                    snippet = snippet_elem.get_text(strip=True)
                    if url and title and snippet:
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })

                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[WARN] Search error for '{q}': {e}")
    return results

def web_search(query: str, max_results: int = None) -> list[dict]:
    limit = max_results or MAX_SEARCH_RESULTS
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    timeout = httpx.Timeout(8.0, connect=4.0)

    results = _execute_search(query, limit, headers, timeout)

    # Fallback to simplified query if zero hits
    if not results:
        simplified = simplify_query(query)
        if simplified and simplified.lower() != query.lower():
            results = _execute_search(simplified, limit, headers, timeout)

    return results
