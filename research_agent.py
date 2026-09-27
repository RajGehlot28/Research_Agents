import os
from graph.workflow import app

def run_research(query: str) -> dict:
    max_iteration = os.getenv("MAX_ITERATIONS")

    print(" RESEARCH-X: AUTONOMOUS MULTI-AGENT RESEARCH SYSTEM")
    print(f"Query: {query}")
    print(f"Max Iterations: {max_iteration}\n")

    initial_state = {
        "query": query,
        "research_plan": [],
        "research_tasks": [],
        "research_results": [],
        "sources": [],
        "verified_claims": [],
        "rejected_claims": [],
        "missing_information": [],
        "iteration": 0,
        "max_iterations": max_iteration,
        "evidence_sufficient": False,
        "final_report": "",
        "current_agent": "planner_agent",
        "status": "in_progress",
        "logs": []
    }

    # invoking the graph
    final_state = app.invoke(initial_state)

    print(f"Total Sources Consulted : {len(final_state['sources'])}")
    print(f"Total Iterations        : {final_state['iteration']}")

    report = final_state['final_report']
    print(report)

    return final_state

if __name__ == "__main__":
    query_input = input("Enter Research Query: ").strip()
    if query_input:
        run_research(query_input)
