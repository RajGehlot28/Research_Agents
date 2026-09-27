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

    if not data or "tasks" not in data:
        # Fallback plan if JSON parsing failed
        tasks = [
            {
                "id": "task_1",
                "title": "Technical Architecture and Capabilities",
                "description": f"Analyze technical details for {query}",
                "role": "Technical Researcher",
                "search_queries": [f"{query} architecture", f"{query} benchmarks"]
            },
            {
                "id": "task_2",
                "title": "Market Adoption and Ecosystem",
                "description": f"Investigate adoption and production usage for {query}",
                "role": "Market Researcher",
                "search_queries": [f"{query} production adoption", f"{query} ecosystem"]
            },
            {
                "id": "task_3",
                "title": "Cost and Practicality",
                "description": f"Evaluate operational costs and complexity for {query}",
                "role": "Cost/Practicality Researcher",
                "search_queries": [f"{query} pricing cost", f"{query} operational trade-offs"]
            }
        ]
        plan_summary = f"Default multi-angle research plan for: {query}"
    else:
        tasks = data.get("tasks", [])
        plan_summary = data.get("plan_summary", "Structured research plan generated.")

    # Mark all tasks as pending
    for t in tasks:
        t["status"] = "pending"

    logs = state.get("logs", [])
    log_msg = f"[Planner] Created plan with {len(tasks)} tasks."
    logs.append(log_msg)
    print(log_msg, flush=True)

    return {
        "research_plan": [{"summary": plan_summary, "total_tasks": len(tasks)}],
        "research_tasks": tasks,
        "current_agent": "researcher_agent",
        "logs": logs
    }
