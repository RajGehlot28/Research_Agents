from typing import TypedDict

class ResearchState(TypedDict):
    query: str
    research_plan: list
    research_tasks: list
    research_results: list
    sources: list
    verified_claims: list
    rejected_claims: list
    missing_information: list
    iteration: int
    max_iterations: int
    evidence_sufficient: bool
    final_report: str
    current_agent: str
    status: str
    logs: list
