from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry
from agents.utils import parse_json_response

SYSTEM_PROMPT = """You are a Follow-up Research Agent in an autonomous multi-agent research system.
Your job is to generate targeted follow-up research tasks to address missing information, gaps, or rejected claims identified by the Critic Agent.

Guidelines:
- Generate 1 to 3 very specific, targeted follow-up tasks.
- Assign each task to the most suitable researcher role ('Technical Researcher', 'Market Researcher', 'Cost/Practicality Researcher').
- Provide precise, effective search queries that target the missing data.

Return ONLY a JSON object with this exact structure:
{
  "followup_summary": "Brief summary of what this follow-up research aims to resolve",
  "new_tasks": [
    {
      "id": "followup_1",
      "title": "Clear follow-up task title",
      "description": "Specific focus of this follow-up task",
      "role": "Technical Researcher",
      "search_queries": ["targeted query 1", "targeted query 2"]
    }
  ]
}
"""

def followup_agent(state: ResearchState) -> dict:
    iteration = state["iteration"] + 1
    query = state["query"]
    missing = state["missing_information"]
    rejected = state["rejected_claims"]
    tasks = list(state["research_tasks"])
    logs = list(state["logs"])
    missing_text = "\n".join([f"- {m}" for m in missing]) if missing else "General depth and verification required."
    rejected_text = "\n".join([f"- {r.get('claim')}: {r.get('reason')}" for r in rejected]) if rejected else "None"

    prompt = (
        f"Original Query: {query}\n"
        f"Missing Information Identified by Critic:\n{missing_text}\n\n"
        f"Rejected Claims to Re-examine:\n{rejected_text}\n"
    )

    llm = get_llm("followup")
    response = invoke_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    parsed = parse_json_response(extract_text(response))

    if parsed and "new_tasks" in parsed:
        new_tasks = parsed["new_tasks"]
    else:
        new_tasks = [
            {
                "id": f"followup_{iteration}_1",
                "title": f"Targeted Deep-dive on Missing Gaps",
                "description": f"Gather missing data for: {missing[:2]}",
                "role": "Technical Researcher",
                "search_queries": [f"{query} benchmark details", f"{query} comparison"]
            }
        ]

    for t in new_tasks:
        t["status"] = "pending"
        tasks.append(t)

    log_msg = f"[Follow-up] Iteration {iteration}: added {len(new_tasks)} follow-up tasks."
    logs.append(log_msg)
    print(log_msg)

    return {
        "research_tasks": tasks,
        "iteration": iteration,
        "current_agent": "researcher_agent",
        "logs": logs
    }
