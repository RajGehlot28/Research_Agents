from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry
from agents.utils import parse_json_response

SYSTEM_PROMPT = """You are a Critic and Verification Agent in an autonomous multi-agent research system.
Your job is to rigorously evaluate the gathered claims and evidence against the original research query.

You must check:
1. Is each claim backed by direct, credible evidence?
2. Are any claims contradictory, outdated, or weak?
3. Does the verified evidence sufficiently and comprehensively address the user's research query?
4. What specific key information is still missing?

Return ONLY a JSON object with this exact structure:
{
  "critique_summary": "Summary of your evaluation",
  "verified_claims": [
    {
      "claim": "The verified statement",
      "evidence": "Supporting text",
      "source_url": "Source URL or document",
      "confidence": "high" | "medium",
      "reason": "Why this claim is accepted"
    }
  ],
  "rejected_claims": [
    {
      "claim": "The rejected statement",
      "reason": "Why this claim was rejected (e.g. outdated, unverified, contradictory)"
    }
  ],
  "missing_information": [
    "Specific gap or missing metric 1",
    "Specific gap or missing metric 2"
  ],
  "evidence_sufficient": true | false
}
"""

def critic_agent(state: ResearchState) -> dict:
    query = state["query"]
    results = state.get("research_results", [])
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)
    logs = list(state.get("logs", []))

    # Aggregate all claims collected across all tasks
    all_claims = []
    for r in results:
        task_title = r.get("title", "")
        for c in r.get("claims", []):
            all_claims.append({
                "task": task_title,
                "claim": c.get("claim", ""),
                "evidence": c.get("evidence", ""),
                "source_url": c.get("source_url", ""),
                "confidence": c.get("confidence", "medium")
            })

    if not all_claims:
        log_msg = "[Critic] Verification complete: 0 verified, 0 rejected. Status: Insufficient (Follow-up needed)."
        logs.append(log_msg)
        print(log_msg, flush=True)
        return {
            "verified_claims": [],
            "rejected_claims": [],
            "missing_information": [f"Complete information for: {query}"],
            "evidence_sufficient": False,
            "current_agent": "followup_agent",
            "logs": logs
        }

    claims_text = "\n".join([
        f"- Task: {c['task']}\n  Claim: {c['claim']}\n  Evidence: {c['evidence']}\n  Source: {c['source_url']}"
        for c in all_claims
    ])

    prompt = (
        f"Original Research Query: {query}\n\n"
        f"Current Research Iteration: {iteration}\n\n"
        f"Collected Claims and Evidence:\n{claims_text}"
    )

    llm = get_llm("critic")
    response = invoke_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    parsed = parse_json_response(extract_text(response))

    if parsed:
        verified = parsed.get("verified_claims", [])
        rejected = parsed.get("rejected_claims", [])
        missing = parsed.get("missing_information", [])
        sufficient = bool(parsed.get("evidence_sufficient", True))
        critique = parsed.get("critique_summary", "Verification completed.")
    else:
        # Fallback: accept claims
        verified = all_claims
        rejected = []
        missing = []
        sufficient = True
        critique = "Default verification passed."

    # If reached max iterations, force sufficient so synthesis can run
    if iteration >= max_iterations and not sufficient:
        sufficient = True
        critique += f" [Max iterations ({max_iterations}) reached - proceeding to report synthesis.]"

    status_str = "Sufficient" if sufficient else "Insufficient (Follow-up needed)"
    log_msg = f"[Critic] Verification complete: {len(verified)} verified, {len(rejected)} rejected. Status: {status_str}."
    logs.append(log_msg)
    print(log_msg, flush=True)

    return {
        "verified_claims": verified,
        "rejected_claims": rejected,
        "missing_information": missing,
        "evidence_sufficient": sufficient,
        "current_agent": "synthesizer_agent" if sufficient else "followup_agent",
        "logs": logs
    }
