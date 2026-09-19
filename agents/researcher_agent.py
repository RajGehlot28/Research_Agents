from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry
from tools.search_tool import web_search
from tools.fetch_tool import web_fetch
from tools.document_tool import document_search
from agents.utils import parse_json_response

SYSTEM_PROMPT = """You are a Specialized Researcher Agent.
Your job is to analyze gathered research materials (web snippets, fetched pages, internal documents) and extract verified factual claims with supporting evidence.

Role Guidelines:
- Extract factual, concrete claims with direct evidence.
- Identify specific metrics, benchmarks, architectural attributes, or costs where present.
- Every claim MUST reference a source from the provided material.
- Do not invent claims not backed by the text.

Return ONLY a JSON object with this exact structure:
{
  "findings_summary": "Brief summary of key findings for this task",
  "claims": [
    {
      "claim": "Specific factual statement",
      "evidence": "Quotation or summary of supporting text from source",
      "source_url": "URL or document name",
      "source_title": "Title of the source",
      "confidence": "high" | "medium" | "low"
    }
  ]
}
"""

def researcher_agent(state: ResearchState) -> dict:
    tasks = state.get("research_tasks", [])
    results = list(state.get("research_results", []))
    sources = list(state.get("sources", []))
    logs = list(state.get("logs", []))
    existing_urls = {s.get("url") for s in sources if s.get("url")}

    llm = get_llm()

    # Process pending tasks
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]
    if not pending_tasks:
        print("[Researcher Agent] No pending tasks to process.")
        return {"current_agent": "critic_agent"}

    print(f"[Researcher Agent] Executing {len(pending_tasks)} research tasks.")

    for task in pending_tasks:
        role = task.get("role", "Technical Researcher")
        title = task.get("title", "")
        task_id = task.get("id", "")
        queries = task.get("search_queries", [title])

        print(f"[{role}] Starting task: {title}")

        # Gather web search results
        search_hits = []
        for q in queries[:2]:
            hits = web_search(q, max_results=3)
            search_hits.extend(hits)

        # Gather document search results
        doc_hits = document_search(title, max_results=2)

        # Register sources
        for hit in search_hits:
            url = hit.get("url")
            if url and url not in existing_urls:
                existing_urls.add(url)
                sources.append({
                    "id": f"src_{len(sources) + 1}",
                    "title": hit.get("title", "Web Source"),
                    "url": url,
                    "snippet": hit.get("snippet", ""),
                    "type": "web"
                })

        for d in doc_hits:
            src_name = d.get("source", "Document")
            sources.append({
                "id": f"src_{len(sources) + 1}",
                "title": src_name,
                "url": src_name,
                "snippet": d.get("text", "")[:300],
                "type": "document"
            })

        # Optionally fetch the top web page if available
        fetched_content = ""
        if search_hits and search_hits[0].get("url"):
            top_url = search_hits[0]["url"]
            print(f"[{role}] Fetching deep content from: {top_url[:60]}...")
            fetched_content = web_fetch(top_url, max_chars=3000)

        # Compile research context for LLM extraction
        context_blocks = []
        if search_hits:
            context_blocks.append("--- Web Search Results ---")
            for h in search_hits:
                context_blocks.append(f"Title: {h.get('title')}\nURL: {h.get('url')}\nSnippet: {h.get('snippet')}\n")

        if doc_hits:
            context_blocks.append("--- Internal Document Results ---")
            for d in doc_hits:
                context_blocks.append(f"File: {d.get('source')}\nContent: {d.get('text')}\n")

        if fetched_content and not fetched_content.startswith("Error"):
            context_blocks.append("--- Fetched Page Content ---")
            context_blocks.append(fetched_content[:2500])

        raw_context = "\n".join(context_blocks)
        if not raw_context.strip():
            raw_context = f"No external search results were retrieved for queries: {queries}. Rely on baseline verified facts."

        extraction_prompt = (
            f"Research Task: {title}\n"
            f"Role: {role}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Gathered Evidence:\n{raw_context}"
        )

        response = invoke_with_retry(llm, [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=extraction_prompt)
        ])

        parsed = parse_json_response(extract_text(response))
        findings_summary = ""
        claims = []

        if parsed:
            findings_summary = parsed.get("findings_summary", "")
            claims = parsed.get("claims", [])
        else:
            findings_summary = extract_text(response)[:400]
            claims = [{
                "claim": f"Findings for {title}",
                "evidence": findings_summary,
                "source_url": search_hits[0].get("url") if search_hits else "baseline",
                "source_title": search_hits[0].get("title") if search_hits else "General",
                "confidence": "medium"
            }]

        task["status"] = "completed"
        results.append({
            "task_id": task_id,
            "title": title,
            "role": role,
            "findings_summary": findings_summary,
            "claims": claims
        })

        print(f"[{role}] Completed task with {len(claims)} extracted claims.")
        logs.append(f"[{role}] Completed task '{title}' ({len(claims)} claims).")

    return {
        "research_tasks": tasks,
        "research_results": results,
        "sources": sources,
        "current_agent": "critic_agent",
        "logs": logs
    }
