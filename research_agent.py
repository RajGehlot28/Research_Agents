import sys
import os
import time

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["PYTHONUNBUFFERED"] = "1"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass
from graph.workflow import app

def run_research(query: str, max_iterations: int = None) -> dict:
    if not query.strip():
        print("[ERROR] Query cannot be empty.")
        return {}

    max_iter = max_iterations or int(os.getenv("MAX_ITERATIONS", "2"))

    print("\n" + "=" * 60)
    print(" RESEARCH-X: AUTONOMOUS MULTI-AGENT RESEARCH SYSTEM")
    print("=" * 60)
    print(f"Query: {query}")
    print(f"Max Verification Iterations: {max_iter}\n")

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
        "max_iterations": max_iter,
        "evidence_sufficient": False,
        "final_report": "",
        "current_agent": "planner_agent",
        "status": "in_progress",
        "logs": []
    }

    start_time = time.time()
    final_state = app.invoke(initial_state)
    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print(f" RESEARCH COMPLETED (Time: {elapsed:.2f}s)")
    print("=" * 60)
    print(f"Total Sources Consulted : {len(final_state.get('sources', []))}")
    print(f"Verified Claims         : {len(final_state.get('verified_claims', []))}")
    print(f"Rejected Claims         : {len(final_state.get('rejected_claims', []))}")
    print(f"Total Iterations        : {final_state.get('iteration', 0)}")
    print("=" * 60 + "\n")

    report = final_state.get("final_report", "")
    print(report)

    # Save report locally
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    safe_name = "".join([c if c.isalnum() else "_" for c in query[:30]])
    report_file = os.path.join(reports_dir, f"report_{safe_name}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[OK] Report saved to: {report_file}")

    return final_state

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_input = " ".join(sys.argv[1:])
    else:
        query_input = input("Enter Research Query: ").strip()

    if query_input:
        run_research(query_input)
