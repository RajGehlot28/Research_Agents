from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry
from agents.utils import make_links_clickable

SYSTEM_PROMPT = """You are an expert Synthesizer Agent in an autonomous multi-agent research system.
Your job is to synthesize all verified claims, research findings, and sources into an exhaustive, highly structured, citation-backed research report.

You MUST format the report using these exact sections:

Title & Executive Summary
[A clear title followed by comprehensive executive summary paragraphs explaining the foundational decision, core comparative analysis, technical trade-offs, and operational takeaways.]

Detailed Findings & Technical Analysis
[Detailed subheadings for each primary technology/architectural area. Provide in-depth technical paragraphs explaining architectural patterns, isolation pathways, scalability limitations, data integrity mechanisms, and benchmarks with citations.]

Comparative Analysis & Trade-offs
[Include a comprehensive Markdown comparison table comparing key dimensions, for example:
| Feature / Dimension | [Option A] | [Option B] |
Follow the table with detailed paragraphs analyzing critical trade-offs such as licensing constraints (e.g. SSPL vs permissive licenses), data consistency, and operational complexities.]

Practical & Operational Considerations
[Detailed subsections on:
- Cloud Hosting and Free Tiers (compare cloud provider instances, storage, and free tier limitations)
- Operational Risks and Mitigation (concrete, actionable mitigations for identified architectural risks)]

Recommendations & Conclusion
[Actionable strategic guidance divided into:
- When to Choose [Option A] (criteria and specific Implementation Strategy)
- When to Choose [Option B] (criteria and specific Implementation Strategy)]

References & Citations
[A clean, numbered list of all consulted sources with clickable Markdown links for valid URLs, in the format:
[X] Title
URL: [URL](URL) (or if no URL is available: URL: baseline)
]

Formatting Guidelines:
- Write in rich, rigorous, articulate technical prose with high factual density.
- Do NOT use emojis.
- Use numbered in-text citations like [1], [2] corresponding to the sources provided.
- Format all URLs in the References & Citations section as clickable Markdown links: `URL: [https://...](https://...)`.
- Ensure all claims directly answer the research question based on the verified evidence.
"""

def synthesizer_agent(state: ResearchState) -> dict:
    query = state["query"]
    verified = state.get("verified_claims", [])
    sources = state.get("sources", [])
    logs = list(state.get("logs", []))

    # Build reference mapping
    source_map_text = []
    for idx, s in enumerate(sources, 1):
        title = s["title"]
        url = s["url"]
        source_map_text.append(f"[{idx}] {title}\nURL: [{url}]({url})")

    references_block = "\n".join(source_map_text) if source_map_text else "No external sources registered."

    claims_text = "\n".join([
        f"- Claim: {v.get('claim')}\n  Evidence: {v.get('evidence')}\n  Source: {v.get('source_url')}"
        for v in verified
    ])

    prompt = (
        f"Research Question: {query}\n\n"
        f"Verified Claims & Evidence:\n{claims_text}\n\n"
        f"Available Sources for Citations:\n{references_block}\n"
    )

    llm = get_llm("synthesizer")
    response = invoke_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    report = extract_text(response)
    report = make_links_clickable(report)
    log_msg = "[Synthesizer Agent] Generated final citation-backed report."
    logs.append(log_msg)
    print(log_msg)

    return {
        "final_report": report,
        "sources": sources,
        "current_agent": "end",
        "status": "completed",
        "logs": logs
    }
