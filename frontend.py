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

DOCUMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "documents"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

st.set_page_config(
    page_title="Research-X Control Center",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="brand-badge">
            <strong>Research-X Control Center</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### System Configuration")
    st.caption(f"Model: {GEMINI_MODEL} (Google Gemini)")
    max_iter = st.slider("Max Verification Iterations", min_value=1, max_value=4, value=MAX_ITERATIONS)

    st.divider()

    st.markdown("### Internal Document Upload (RAG)")
    uploaded_files = st.file_uploader(
        "Upload files for internal research",
        type=["txt", "md", "pdf", "json"],
        accept_multiple_files=True
    )
    if uploaded_files:
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        for uf in uploaded_files:
            fpath = os.path.join(DOCUMENTS_DIR, uf.name)
            with open(fpath, "wb") as f:
                f.write(uf.getbuffer())
        st.success(f"Indexed {len(uploaded_files)} document(s) for RAG.")

    st.divider()

    st.markdown("### Suggested Topics")
    suggestions = [
        "Compare PostgreSQL and MongoDB for a multi-tenant SaaS",
        "Compare the latest open-source LLMs for building a production RAG application",
        "Compare SQLite and DuckDB for local analytics",
        "Evaluate Qdrant vs pgvector for scalable vector search"
    ]

    selected_query = None
    for s in suggestions:
        if st.button(s, use_container_width=True):
            selected_query = s

    st.divider()
    st.markdown("### Demo Showcase")
    if st.button("Load Pre-Generated Sample Report", use_container_width=True):
        sample_path = os.path.join(os.path.dirname(__file__), "reports", "report_Compare_PostgreSQL_and_MongoDB.md")
        report_text = ""
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                report_text = f.read()

        st.session_state.research_state = {
            "query": "Compare PostgreSQL and MongoDB for a multi-tenant SaaS",
            "research_plan": [
                {"title": "Multi-Tenant Architecture", "specialization": "Technical"},
                {"title": "Performance & Scalability", "specialization": "Technical"},
                {"title": "Licensing & TCO", "specialization": "Cost"}
            ],
            "research_tasks": [
                {"description": "Investigate PostgreSQL row-level security and schema isolation", "status": "completed"},
                {"description": "Benchmark MongoDB horizontal sharding under multi-tenant load", "status": "completed"},
                {"description": "Analyze SSPL license restrictions vs PostgreSQL permissive license", "status": "completed"}
            ],
            "sources": [
                {"title": "PostgreSQL SaaS Multi-Tenant Architecture Guide", "url": "https://devcerts.org/blog/postgresql-for-saas-tenant-isolation-rls-and-restore-strategy", "type": "web"},
                {"title": "Multi-tenant SaaS partitioning models for PostgreSQL (AWS)", "url": "https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/partitioning-models.html", "type": "web"},
                {"title": "MongoDB Benchmark Suite", "url": "https://www.mongodb.com/resources/compare/mongodb-benchmark", "type": "web"}
            ],
            "verified_claims": [
                {"claim": "PostgreSQL supports shared tables with tenant_id, schema-per-tenant, and database-per-tenant models.", "evidence": "Documented in AWS multi-tenant prescriptive guidance and devcerts architecture guide.", "source_url": "https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/partitioning-models.html"},
                {"claim": "PostgreSQL provides full ACID compliance critical for complex financial transactions in multi-tenant systems.", "evidence": "Verified across engine architectural specifications.", "source_url": "https://devcerts.org/blog/postgresql-for-saas-tenant-isolation-rls-and-restore-strategy"},
                {"claim": "MongoDB operates under the Server Side Public License (SSPL) which places restrictions on commercial cloud hosting.", "evidence": "Confirmed via MongoDB licensing documentation.", "source_url": "https://github.com/mongodb/mongo-perf"}
            ],
            "rejected_claims": [
                {"claim": "MongoDB does not support multi-document ACID transactions.", "reason": "Contradicted: MongoDB introduced multi-document ACID transactions starting in version 4.0."}
            ],
            "iteration": 1,
            "max_iterations": 2,
            "evidence_sufficient": True,
            "final_report": report_text,
            "logs": [
                "[Planner] Generated 3 specialized research tracks: Technical, Performance, Licensing",
                "[Researcher] Executed 3 web investigations across 6 primary sources",
                "[Critic] Verified 3 claims; rejected 1 outdated claim regarding MongoDB transactions",
                "[Critic] Evidence sufficiency check passed. Routing to Synthesizer",
                "[Synthesizer] Compiled executive report with 6 indexed citations"
            ]
        }
        st.session_state.is_running = False
        st.rerun()

    st.divider()
    if st.button("Reset Session", use_container_width=True):
        st.session_state.research_state = None
        st.session_state.is_running = False
        st.rerun()

# Main Interface
st.title("Research-X: Autonomous Multi-Agent Research System")
st.caption("Decomposes queries -> executes parallel research -> verifies evidence -> resolves gaps -> synthesizes citation-backed reports.")

query_input = st.text_area(
    "Enter Research Query:",
    value=selected_query if selected_query else "",
    placeholder="e.g. Compare the latest open-source LLMs for building a production RAG application.",
    height=90
)

start_clicked = st.button("Start Autonomous Research", type="primary", use_container_width=True)

if start_clicked and query_input.strip():
    st.session_state.is_running = True
    initial_state = {
        "query": query_input.strip(),
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

    with st.spinner("Multi-agent workflow in progress... (Planning -> Research -> Verification -> Synthesis)"):
        try:
            final_result = workflow_app.invoke(initial_state)
            st.session_state.research_state = final_result
            st.session_state.is_running = False
            st.success("Research completed successfully.")
        except Exception as err:
            st.session_state.is_running = False
            st.error(f"Error during research execution: {str(err)}")

# Results Display
res = st.session_state.research_state
if res:
    st.divider()

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
                <div class="metric-value">{len(res.get('sources', []))}</div>
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

    tab1, tab2, tab3, tab4 = st.tabs([
        "Final Report",
        "Verified Claims & Evidence",
        "Sources & References",
        "System Trace"
    ])

    with tab1:
        report_md = res.get("final_report", "")
        if report_md:
            st.markdown(report_md)
            st.download_button(
                label="Download Markdown Report",
                data=report_md,
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.info("No report generated.")

    with tab2:
        verified = res.get("verified_claims", [])
        rejected = res.get("rejected_claims", [])

        st.subheader(f"Verified Claims ({len(verified)})")
        for idx, vc in enumerate(verified, 1):
            st.markdown(
                f"""
                <div class="claim-box">
                    <strong>Claim {idx}:</strong> {vc.get('claim')}<br>
                    <small style="color: #8b949e;">Evidence: {vc.get('evidence')}</small><br>
                    <small style="color: #58a6ff;">Source: {vc.get('source_url')}</small>
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
        sources = res.get("sources", [])
        st.subheader(f"Registered Sources ({len(sources)})")
        for idx, s in enumerate(sources, 1):
            with st.expander(f"[{idx}] {s.get('title', 'Source')}"):
                st.write(f"**URL / Path:** {s.get('url')}")
                st.write(f"**Type:** {s.get('type')}")
                if s.get("snippet"):
                    st.caption(f"**Snippet:** {s.get('snippet')}")

    with tab4:
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
