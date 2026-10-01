try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = None) -> list[dict]:
    limit = max_results
    results = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=limit):
                title = item.get("title", "")
                url = item.get("href", "")
                snippet = item.get("body", "")

                if url and title:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
    except Exception as e:
        print(f"[WARN] Search error for '{query}': {e}")

    return results
