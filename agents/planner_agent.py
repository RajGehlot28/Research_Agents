from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from config.llm import get_llm, extract_text, invoke_with_retry
from agents.utils import parse_json_response

SYSTEM_PROMPT = """You are a Research Planner Agent in an autonomous multi-agent research system.
Your goal is to understand the user's research question and produce a structured research plan.
Decompose the query into 3 to 5 targeted tasks, each assigned to a specialized researcher role:
- 'Technical Researcher': Architecture, technical capabilities, benchmarks, performance, APIs.
- 'Market Researcher': Ecosystem, real-world adoption, community, licensing, production use-cases.
- 'Cost/Practicality Researcher': Pricing, resource requirements, operational overhead, scalability costs.

Return ONLY a JSON object with this exact structure (no markdown fences, no conversational text):
{
  "plan_summary": "Brief summary of the research strategy",
  "tasks": [
    {
      "id": "task_1",
      "title": "Clear task title",
      "description": "Specific focus of this research task",
      "role": "Technical Researcher",
      "search_queries": ["query 1", "query 2"]
    }
  ]
}
"""

def planner_agent(state: ResearchState) -> dict:
    query = state["query"]

    llm = get_llm("planner")
    prompt = f"Research Query: {query}"

    response = invoke_with_retry(llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    raw_text = extract_text(response)
    data = parse_json_response(raw_text)

    tasks = data["tasks"]
    plan_summary = data["plan_summary"]

    # Mark all tasks as pending
    for t in tasks:
        t["status"] = "pending"

    # storing logs to display on frontend
    logs = state["logs"]
    log_msg = f"[Planner Agent] Created plan with {len(tasks)} tasks."
    logs.append(log_msg)
    print(log_msg)

    return {
        "research_plan": [{"summary": plan_summary, "total_tasks": len(tasks)}],
        "research_tasks": tasks,
        "current_agent": "researcher_agent",
        "logs": logs
    }
