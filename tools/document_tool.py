import os

DOCUMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "documents"))
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

def read_file_content(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in [".txt", ".md", ".json", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                return "\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception:
                return ""
    except Exception as e:
        print(f"[WARN] Error reading {file_path}: {e}")
    return ""

def document_search(query: str, max_results: int = 3) -> list[dict]:
    if not os.path.exists(DOCUMENTS_DIR):
        return []

    query_terms = [t.lower() for t in query.split() if len(t) > 2]
    matched_chunks = []

    for root, _, files in os.walk(DOCUMENTS_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            content = read_file_content(file_path)
            if not content:
                continue

            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
            for p in paragraphs:
                p_lower = p.lower()
                matches = sum(1 for term in query_terms if term in p_lower)
                if matches > 0:
                    matched_chunks.append({
                        "source": file,
                        "score": matches,
                        "text": p[:1000]
                    })

    matched_chunks.sort(key=lambda x: x["score"], reverse=True)
    return matched_chunks[:max_results]
