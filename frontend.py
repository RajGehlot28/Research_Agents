import sys
import os
import json
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Ensure UTF-8 output encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import streamlit as st
from graph.workflow import app as workflow_app
from agents.utils import make_links_clickable

MAX_ITERATIONS = 4
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

st.set_page_config(
    page_title="Research-X: Autonomous Multi-Agent Research System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Dark Styling (Strictly No Emojis)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #161b22;
        border: 1px solid #30363d;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 14px;
        color: #58a6ff;
        margin-bottom: 15px;
    }
    .status-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 12px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .claim-box {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    .claim-rejected {
        background: #161b22;
        border-left: 3px solid #f85149;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Session state initialization
if "research_state" not in st.session_state:
    st.session_state.research_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "research_query" not in st.session_state:
    st.session_state.research_query = ""

# Main Interface
st.title("Research-X: Autonomous Multi-Agent Research System")

def start_research_callback():
    if (st.session_state.get("research_query") or "").strip():
        st.session_state.is_running = True

query_input = st.text_area(
    "Enter Research Query:",
    placeholder="e.g. Compare PostgreSQL and MongoDB for a multi-tenant SaaS application.",
    height=90,
    key="research_query",
    disabled=st.session_state.is_running
)

start_clicked = st.button(
    "Research in Progress..." if st.session_state.is_running else "Start Research",
    type="primary",
    use_container_width=True,
    disabled=st.session_state.is_running,
    on_click=start_research_callback
)

if start_clicked and not (st.session_state.get("research_query") or "").strip():
    st.warning("Please enter a research query to begin.")

if st.session_state.is_running:
    clean_query = (st.session_state.research_query or "").strip()
    initial_state = {
        "query": clean_query,
        "research_plan": [],
        "research_tasks": [],
        "research_results": [],
        "sources": [],
        "verified_claims": [],
        "rejected_claims": [],
        "missing_information": [],
        "iteration": 0,
        "max_iterations": MAX_ITERATIONS,
        "evidence_sufficient": False,
        "final_report": "",
        "current_agent": "planner_agent",
        "status": "in_progress",
        "logs": []
    }

    with st.status("Initializing research workflow...", expanded=True) as status_box:
        try:
            final_result = initial_state
            agent_display_names = {
                "planner_agent": "Planner Agent (Decomposing research query into specialized tracks)",
                "researcher_agent": "Researcher Agent (Executing web searches and evidence extraction)",
                "critic_agent": "Critic Agent (Verifying claims and checking evidence sufficiency)",
                "followup_agent": "Follow-up Agent (Formulating targeted follow-up research tasks)",
                "synthesizer_agent": "Synthesizer Agent (Compiling citation-backed executive report)"
            }
            displayed_logs_count = 0
            for step_state in workflow_app.stream(initial_state, stream_mode="values"):
                final_result = step_state
                curr_agent = step_state.get("current_agent", "")
                if curr_agent in agent_display_names:
                    status_box.update(label=f"Running: {agent_display_names[curr_agent]}")

                current_logs = step_state.get("logs", [])
                while displayed_logs_count < len(current_logs):
                    status_box.write(f"- {current_logs[displayed_logs_count]}")
                    displayed_logs_count += 1

            st.session_state.research_state = final_result
            st.session_state.is_running = False
            status_box.update(label="Research completed successfully!", state="complete", expanded=False)
            st.success("Research completed successfully.")
            st.rerun()
        except Exception as err:
            st.session_state.is_running = False
            status_box.update(label="Research encountered an error", state="error", expanded=True)
            st.error(f"Error during research execution: {str(err)}")
            st.rerun()

# Results Display
res = st.session_state.research_state
if res:
    st.divider()

    # Calculate sources consulted (fallback to references in report or verified claims if empty)
    sources_count = len(res.get("sources", []))
    if sources_count == 0:
        report_text = res.get("final_report", "")
        if report_text:
            import re
            ref_section = re.search(r"(?:###?\s*(?:References|Sources|Citations)[\s\S]*$)", report_text, re.IGNORECASE)
            target_text = ref_section.group(0) if ref_section else report_text
            ref_items = re.findall(r"(?:^|\n)\s*(?:\[\d+\]|\d+[\.\)])\s+[^\n]+", target_text)
            if ref_items:
                sources_count = len(ref_items)
            else:
                cits = set(re.findall(r"\[(\d+)\]", report_text))
                if cits:
                    sources_count = len(cits)
                else:
                    urls = set(re.findall(r"https?://[^\s\)\]]+", target_text))
                    if urls:
                        sources_count = len(urls)

        if sources_count == 0:
            verified_urls = {
                vc.get("source_url")
                for vc in res.get("verified_claims", [])
                if vc.get("source_url") and vc.get("source_url") not in ("baseline", "None", "")
            }
            if verified_urls:
                sources_count = len(verified_urls)

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(res.get('research_tasks', []))}</div>
                <div class="metric-label">Tasks Executed</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{sources_count}</div>
                <div class="metric-label">Sources Consulted</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(res.get('verified_claims', []))}</div>
                <div class="metric-label">Verified Claims</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{res.get('iteration', 0)}</div>
                <div class="metric-label">Verification Loops</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    tab1, tab2, tab3 = st.tabs([
        "Research Response",
        "Verified Claims & Evidence",
        "System Trace"
    ])

    with tab1:
        report_md = res.get("final_report", "")
        if report_md:
            formatted_report = make_links_clickable(report_md)
            st.markdown(formatted_report)
            st.download_button(
                label="Download Response",
                data=formatted_report,
                file_name="research_response.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.info("No response generated.")

    with tab2:
        verified = res.get("verified_claims", [])
        rejected = res.get("rejected_claims", [])

        st.subheader(f"Verified Claims ({len(verified)})")
        for idx, vc in enumerate(verified, 1):
            src_url = vc.get("source_url", "")
            if src_url and src_url.startswith(("http://", "https://")):
                source_display = f'<a href="{src_url}" target="_blank" style="color: #58a6ff; text-decoration: underline;">{src_url}</a>'
            else:
                source_display = src_url

            st.markdown(
                f"""
                <div class="claim-box">
                    <strong>Claim {idx}:</strong> {vc.get('claim')}<br>
                    <small style="color: #8b949e;">Evidence: {vc.get('evidence')}</small><br>
                    <small style="color: #58a6ff;">Source: {source_display}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

        if rejected:
            st.subheader(f"Rejected or Contradicted Claims ({len(rejected)})")
            for idx, rc in enumerate(rejected, 1):
                st.markdown(
                    f"""
                    <div class="claim-rejected">
                        <strong>Rejected Claim {idx}:</strong> {rc.get('claim')}<br>
                        <small style="color: #8b949e;">Reason: {rc.get('reason')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab3:
        st.subheader("Multi-Agent Execution Logs")
        logs = res.get("logs", [])
        for l in logs:
            st.text(l)

        with st.expander("Raw State Dump", expanded=False):
            st.json({
                "query": res.get("query"),
                "tasks": res.get("research_tasks"),
                "iteration": res.get("iteration"),
                "evidence_sufficient": res.get("evidence_sufficient")
            })