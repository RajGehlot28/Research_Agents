from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry

SYSTEM_PROMPT = """You are a Synthesizer Agent in an autonomous multi-agent research system.
Your job is to synthesize all verified claims, research findings, and sources into an exhaustive, highly structured, citation-backed research report.

Report Formatting Guidelines:
- Do NOT use any emojis. Keep the presentation professional, analytical, and objective.
- Use numbered in-text citations like [1], [2], [3] corresponding to the sources provided.
- Include the following clear markdown sections:
  # Title & Executive Summary
  ## Detailed Findings & Technical Analysis
  ## Comparative Analysis & Trade-offs
  ## Practical & Operational Considerations
  ## Recommendations & Conclusion
  ## References & Citations

Under '## References & Citations', list each source with its citation number, title, and URL (e.g. `[1] Title - URL`).
Ensure the findings directly answer the original query and reflect the verified facts.
"""

def synthesizer_agent(state: ResearchState) -> dict:
    query = state["query"]
    verified = state.get("verified_claims", [])
    sources = state.get("sources", [])
    logs = list(state.get("logs", []))

    print(f"[Synthesizer Agent] Generating final report with {len(verified)} verified claims and {len(sources)} sources...")

    # Build reference mapping
    source_map_text = []
    for idx, s in enumerate(sources, 1):
        title = s.get("title", "Reference")
        url = s.get("url", "")
        source_map_text.append(f"[{idx}] {title} - {url}")

    references_block = "\n".join(source_map_text) if source_map_text else "No external sources registered."

    claims_text = "\n".join([
        f"- Claim: {v.get('claim')}\n  Evidence: {v.get('evidence')}\n  Source: {v.get('source_url')}"
        for v in verified
    ]) if verified else "Rely on verified foundation knowledge."

    prompt = (
        f"Research Question: {query}\n\n"
        f"Verified Claims & Evidence:\n{claims_text}\n\n"
        f"Available Sources for Citations:\n{references_block}\n"
    )

    llm = get_llm()
    response = invoke_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    report = extract_text(response)
    print("[Synthesizer Agent] Final report generated successfully.")
    logs.append("[Synthesizer] Generated final citation-backed report.")

    return {
        "final_report": report,
        "sources": sources,
        "current_agent": "end",
        "status": "completed",
        "logs": logs
    }
