from langgraph.graph import StateGraph, START, END
from graph.state import ResearchState
from agents.planner_agent import planner_agent
from agents.researcher_agent import researcher_agent
from agents.critic_agent import critic_agent
from agents.followup_agent import followup_agent
from agents.synthesizer_agent import synthesizer_agent

def route_after_critic(state: ResearchState) -> str:
    iteration = state["iteration"]
    max_iter = state["max_iterations"]

    if state["evidence_sufficient"] is True:
        return "synthesizer_agent"

    if iteration >= max_iter:
        return "synthesizer_agent"

    return "followup_agent"

def create_workflow():
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner_agent", planner_agent)
    workflow.add_node("researcher_agent", researcher_agent)
    workflow.add_node("critic_agent", critic_agent)
    workflow.add_node("followup_agent", followup_agent)
    workflow.add_node("synthesizer_agent", synthesizer_agent)

    workflow.add_edge(START, "planner_agent")
    workflow.add_edge("planner_agent", "researcher_agent")
    workflow.add_edge("researcher_agent", "critic_agent")

    workflow.add_conditional_edges(
        "critic_agent",
        route_after_critic,
        {
            "synthesizer_agent": "synthesizer_agent",
            "followup_agent": "followup_agent"
        }
    )

    workflow.add_edge("followup_agent", "researcher_agent")
    workflow.add_edge("synthesizer_agent", END)

    return workflow.compile()

app = create_workflow()
