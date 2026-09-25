"""Streamlit Engineering SaaS User Interface for ArchPilot."""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
import streamlit as st

# Configure page layout and metadata
st.set_page_config(
    page_title="ArchPilot | AI Engineering Decision Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Base URL (configurable via env)
API_BASE_URL = os.getenv("ARCHPILOT_API_URL", "http://127.0.0.1:8000")

# Inject Custom SaaS CSS Stylesheet
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}

/* Header & Accent styling */
.main-header {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1e1b4b;
    margin-bottom: 0.25rem;
    letter-spacing: -0.025em;
}

.sub-header {
    font-size: 0.95rem;
    color: #475569;
    margin-bottom: 1.5rem;
}

/* Metric / KPI Cards */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.kpi-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
}

.kpi-title {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #4338ca;
}

/* Timeline pill steps */
.timeline-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin: 1.25rem 0;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
}

.step-pill {
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.step-completed {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
}

.step-active {
    background: #e0e7ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
    animation: pulse 2s infinite;
}

.step-pending {
    background: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

/* Decision Cards */
.decision-card {
    background: #ffffff;
    border-left: 4px solid #6366f1;
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.trace-row {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    background: #f8fafc;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    margin: 0.25rem 0;
    border: 1px solid #e2e8f0;
}

/* Status badges */
.badge-completed {
    background-color: #dcfce7;
    color: #15803d;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-running {
    background-color: #e0e7ff;
    color: #4338ca;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-failed {
    background-color: #fee2e2;
    color: #b91c1c;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def fetch_api(endpoint: str, method: str = "GET", json_body: Optional[dict] = None) -> Any:
    """Helper to query the ArchPilot FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "POST":
                resp = client.post(url, json=json_body)
            else:
                resp = client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ----------------------------------------------------
# Sidebar Navigation
# ----------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ **ArchPilot**")
    st.markdown("*Evidence-Driven Engineering Decision Agent*")
    st.markdown("---")

    view_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "✨ New Task",
            "🚀 Run Workspace",
            "📋 Plan & Traceability",
            "🔍 Tool Activity",
            "📑 Final Result",
            "⚙️ Settings",
        ],
        index=0,
    )

    st.markdown("---")
    st.caption("Backend Status")
    health_res = fetch_api("/health/live")
    if "error" not in health_res:
        st.success("🟢 API Operational")
    else:
        st.error("🔴 API Offline")


# ----------------------------------------------------
# View 1: Dashboard
# ----------------------------------------------------
if view_selection == "📊 Dashboard":
    st.markdown('<div class="main-header">Engineering System Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Overview of agent runs, tool invocations, and quantitative decision pipelines.</div>',
        unsafe_allow_html=True,
    )

    metrics = fetch_api("/api/v1/metrics")
    if "error" in metrics:
        metrics = {"total_runs": 0, "completed_runs": 0, "active_runs": 0, "tool_calls": 0}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-title">Total Runs</div>
                <div class="kpi-value">{metrics.get('total_runs', 0)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-title">Completed</div>
                <div class="kpi-value" style="color: #059669;">{metrics.get('completed_runs', 0)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-title">Active / Running</div>
                <div class="kpi-value" style="color: #d97706;">{metrics.get('active_runs', 0)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="kpi-card">
                <div class="kpi-title">Tool Calls</div>
                <div class="kpi-value" style="color: #7c3aed;">{metrics.get('tool_calls', 0)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c_left, c_right = st.columns([3, 1])
    with c_left:
        st.subheader("Recent Engineering Runs")
    with c_right:
        if st.button("➕ Create New Task", type="primary", use_container_width=True):
            st.session_state["nav_to_new_task"] = True
            st.rerun()

    runs_data = fetch_api("/api/v1/runs?limit=10")
    if isinstance(runs_data, list) and runs_data:
        table_rows = []
        for r in runs_data:
            badge_class = (
                "badge-completed"
                if r["status"] == "COMPLETED"
                else "badge-running"
                if r["status"] in ("RUNNING", "PENDING")
                else "badge-failed"
            )
            table_rows.append({
                "Run ID": r["run_id"],
                "Task": r["task"][:80] + ("..." if len(r["task"]) > 80 else ""),
                "Status": r["status"],
                "Created At": r["created_at"][:19].replace("T", " ") if r.get("created_at") else "-",
            })
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("No runs found in database. Submit an engineering task to start!")


# ----------------------------------------------------
# View 2: Create Task
# ----------------------------------------------------
elif view_selection == "✨ New Task":
    st.markdown('<div class="main-header">Create Engineering Task</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Submit an architecture problem. ArchPilot will normalize requirements, generate a bounded plan, execute tools, and formulate an evidence-driven decision.</div>',
        unsafe_allow_html=True,
    )

    # Preset templates for quick testing
    templates = {
        "Select a template or type your own...": "",
        "Photo Sharing Service Storage Sizing": (
            "Estimate 1-year persistent storage, replication overhead, and peak ingress network bandwidth "
            "for a photo sharing platform with 10M daily active users uploading 3 photos/day at 500KB average size."
        ),
        "High-Throughput Cache Cluster Sizing": (
            "Design an in-memory caching tier for 500,000 read requests per second with an average cached "
            "object size of 2 KB. Apply 80/20 working set rule and determine required 64GB Redis nodes."
        ),
        "Database Write Sharding & IOPS": (
            "Calculate write IOPS and partition sharding requirements for an IoT telemetry platform "
            "handling 100,000 write records/second with 1KB payload size."
        ),
    }

    selected_template = st.selectbox("Task Presets:", list(templates.keys()))
    default_text = templates[selected_template]

    task_input = st.text_area(
        "Engineering Task Description:",
        value=default_text,
        height=140,
        placeholder="Enter your system design or capacity planning challenge...",
    )

    with st.expander("Advanced Constraints (Optional JSON)", expanded=False):
        constraints_input = st.text_area(
            "Constraints JSON:",
            value='{\n  "availability_target": "99.99%",\n  "max_p99_latency_ms": 150,\n  "cloud_provider": "AWS"\n}',
            height=100,
        )

    col1, col2 = st.columns([1, 4])
    with col1:
        submit_btn = st.button("🚀 Launch ArchPilot Run", type="primary", use_container_width=True)

    if submit_btn:
        if not task_input.strip():
            st.error("Please provide a task description.")
        else:
            try:
                parsed_constraints = json.loads(constraints_input) if constraints_input.strip() else {}
            except Exception as e:
                st.error(f"Invalid Constraints JSON: {e}")
                parsed_constraints = {}

            with st.spinner("Submitting task and initializing agentic graph..."):
                payload = {
                    "task": task_input.strip(),
                    "constraints": parsed_constraints,
                }
                res = fetch_api("/api/v1/runs?sync=true", method="POST", json_body=payload)
                if "error" in res:
                    st.error(f"Error starting run: {res['error']}")
                else:
                    st.success(f"Run {res.get('run_id')} executed successfully!")
                    st.session_state["active_run_id"] = res.get("run_id")
                    st.info("Switch to '🚀 Run Workspace' or '📑 Final Result' in the sidebar to review!")


# ----------------------------------------------------
# View 3: Run Workspace
# ----------------------------------------------------
elif view_selection == "🚀 Run Workspace":
    st.markdown('<div class="main-header">Agent Run Workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive inspection of the live agentic execution trajectory: PLAN → ACT → OBSERVE → VALIDATE → RESPOND.</div>',
        unsafe_allow_html=True,
    )

    runs_list = fetch_api("/api/v1/runs?limit=25")
    run_options = [r["run_id"] for r in runs_list] if isinstance(runs_list, list) else []

    selected_run_id = None
    if run_options:
        default_index = 0
        if "active_run_id" in st.session_state and st.session_state["active_run_id"] in run_options:
            default_index = run_options.index(st.session_state["active_run_id"])
        selected_run_id = st.selectbox("Select Active Run:", run_options, index=default_index)

    if not selected_run_id:
        st.warning("No runs available. Please launch a run from the 'New Task' view.")
    else:
        run_data = fetch_api(f"/api/v1/runs/{selected_run_id}")
        events_data = fetch_api(f"/api/v1/runs/{selected_run_id}/events")
        tools_data = fetch_api(f"/api/v1/runs/{selected_run_id}/tools")

        # Top Bar: Run Metadata
        top_col1, top_col2, top_col3 = st.columns([3, 1, 1])
        with top_col1:
            st.markdown(f"**Task:** {run_data.get('task')}")
        with top_col2:
            status_val = run_data.get("status", "UNKNOWN")
            st.markdown(f"**Status:** `{status_val}`")
        with top_col3:
            st.markdown(f"**Created:** `{run_data.get('created_at', '')[:19]}`")

        # Dynamic Workflow Timeline
        st.markdown("#### Agent Workflow Pipeline")
        timeline_html = """<div class="timeline-container">
            <span class="step-pill step-completed">✓ 1. Normalize Task</span>
            <span class="step-pill step-completed">✓ 2. Formulate Plan</span>
            <span class="step-pill step-completed">✓ 3. Tool Execution</span>
            <span class="step-pill step-completed">✓ 4. Observation Loop</span>
            <span class="step-pill step-completed">✓ 5. Validate Evidence</span>
            <span class="step-pill step-completed">✓ 6. Final Decision</span>
        </div>"""
        st.markdown(timeline_html, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["Execution Plan & Steps", "Tool Telemetry", "Audit Event Log"])

        with tab1:
            plan = run_data.get("plan")
            if plan:
                st.markdown(f"**Goal:** {plan.get('goal')}")
                st.markdown("**Assumptions:**")
                for asm in plan.get("assumptions", []):
                    st.markdown(f"- {asm}")

                st.markdown("---")
                st.markdown("##### Execution Steps")
                for s in plan.get("steps", []):
                    st.markdown(
                        f"""<div class="decision-card">
                            <strong>Step {s.get('id')}: {s.get('objective')}</strong><br>
                            <span style="color: #64748b; font-size: 0.85rem;">Tool: <code>{s.get('tool')}</code> | Status: <b>{s.get('status')}</b></span><br>
                            <div class="trace-row">Inputs: {json.dumps(s.get('inputs', {}))}</div>
                            <span style="font-size: 0.8rem; color: #059669;">Success Criteria: {s.get('success_criteria')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Plan has not been generated for this run yet.")

        with tab2:
            if isinstance(tools_data, list) and tools_data:
                st.markdown("##### Tool Invocations & Telemetry")
                for te in tools_data:
                    st.markdown(
                        f"""<div class="decision-card" style="border-left-color: #10b981;">
                            <strong>Tool: {te.get('tool_name')}</strong> (Step {te.get('step_id')})<br>
                            <div class="trace-row">Inputs: {json.dumps(te.get('inputs'))}</div>
                            <div class="trace-row" style="color: #047857;">Result: {te.get('output')}</div>
                            <span style="font-size: 0.8rem; color: #64748b;">Latency: {te.get('duration_ms')} ms | Status: {te.get('status')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No tool telemetry events logged.")

        with tab3:
            if isinstance(events_data, list) and events_data:
                for ev in events_data:
                    st.markdown(
                        f"`{ev.get('timestamp')[:19]}` | **{ev.get('event_type')}** (Step: {ev.get('step_id') or '-'})"
                    )
                    with st.expander(f"Payload: {ev.get('event_type')}", expanded=False):
                        st.json(ev.get("payload", {}))
            else:
                st.info("No audit events recorded.")


# ----------------------------------------------------
# View 4: Plan & Traceability
# ----------------------------------------------------
elif view_selection == "📋 Plan & Traceability":
    st.markdown('<div class="main-header">Plan & Traceability Graph</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Inspect how constraints map directly to calculation evidence and final architecture decisions.</div>',
        unsafe_allow_html=True,
    )

    runs_list = fetch_api("/api/v1/runs?limit=25")
    run_options = [r["run_id"] for r in runs_list] if isinstance(runs_list, list) else []

    if run_options:
        selected_run_id = st.selectbox("Select Run:", run_options)
        result_data = fetch_api(f"/api/v1/runs/{selected_run_id}/result")

        if "decision_trace" in result_data and result_data["decision_trace"]:
            st.markdown("### Decision Traceability Chain")
            st.markdown(
                "*Decision ↓ Constraints ↓ Evidence ↓ Calculation ↓ Trade-off*"
            )
            for idx, trace in enumerate(result_data["decision_trace"]):
                st.markdown(
                    f"""<div class="decision-card">
                        <h4 style="margin: 0 0 0.5rem 0; color: #4338ca;">#{idx+1} {trace.get('decision')}</h4>
                        <div class="trace-row"><b>Constraint:</b> {trace.get('constraint')}</div>
                        <div class="trace-row"><b>Evidence:</b> {trace.get('evidence')}</div>
                        <div class="trace-row" style="color: #047857;"><b>Calculation:</b> {trace.get('calculation')}</div>
                        <div class="trace-row" style="color: #b45309;"><b>Trade-off:</b> {trace.get('trade_off')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No decision trace available for this run.")
    else:
        st.warning("No runs available.")


# ----------------------------------------------------
# View 5: Tool Activity
# ----------------------------------------------------
elif view_selection == "🔍 Tool Activity":
    st.markdown('<div class="main-header">Tool Activity & Evidence Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Audit trail of safe tool executions, deterministic calculations, and duration telemetry.</div>',
        unsafe_allow_html=True,
    )

    runs_list = fetch_api("/api/v1/runs?limit=25")
    run_options = [r["run_id"] for r in runs_list] if isinstance(runs_list, list) else []

    if run_options:
        selected_run_id = st.selectbox("Select Run to inspect tools:", run_options)
        tools_data = fetch_api(f"/api/v1/runs/{selected_run_id}/tools")

        if isinstance(tools_data, list) and tools_data:
            st.dataframe(tools_data, use_container_width=True)
        else:
            st.info("No tool activity recorded for this run.")
    else:
        st.warning("No runs available.")


# ----------------------------------------------------
# View 6: Final Result
# ----------------------------------------------------
elif view_selection == "📑 Final Result":
    st.markdown('<div class="main-header">Final Engineering Decision Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Structured deliverables: Executive Summary, Plan, Actions, Observations, Calculations, and Recommendation.</div>',
        unsafe_allow_html=True,
    )

    runs_list = fetch_api("/api/v1/runs?limit=25")
    run_options = [r["run_id"] for r in runs_list] if isinstance(runs_list, list) else []

    if run_options:
        selected_run_id = st.selectbox("Select Run Report:", run_options)
        res = fetch_api(f"/api/v1/runs/{selected_run_id}/result")

        if "error" in res or "executive_summary" not in res:
            st.warning("Final result report is not ready or failed.")
        else:
            st.markdown(
                f"""<div class="decision-card" style="border-left-color: #4338ca; background: #faf5ff;">
                    <h3 style="margin-top: 0; color: #4338ca;">Executive Summary</h3>
                    <p style="font-size: 1.05rem; line-height: 1.6;">{res.get('executive_summary')}</p>
                </div>""",
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🔍 Observations & Evidence")
                for obs in res.get("observations", []):
                    st.markdown(f"- {obs}")

            with col2:
                st.markdown("#### 🧮 Deterministic Calculations")
                for calc in res.get("calculations", []):
                    st.markdown(
                        f"""<div class="trace-row">
                            <b>{calc.get('metric', 'Metric')}:</b> {calc.get('formula', '')} = <b>{calc.get('result')}</b> {calc.get('unit', '')}
                        </div>""",
                        unsafe_allow_html=True,
                    )

            st.markdown("---")
            st.markdown("### 🏛️ Architectural Decision & Specification")
            st.markdown(res.get("final_answer", ""))

            st.markdown("---")
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown("#### ⚖️ Technical Trade-offs")
                for to in res.get("trade_offs", []):
                    st.markdown(f"- ⚠️ {to}")

            with c_right:
                st.markdown("#### 🛡️ Scalability & Operational Risks")
                for rsk in res.get("risks", []):
                    st.markdown(f"- 🔴 {rsk}")
    else:
        st.warning("No runs available.")


# ----------------------------------------------------
# View 7: Settings
# ----------------------------------------------------
elif view_selection == "⚙️ Settings":
    st.markdown('<div class="main-header">System Settings & Configuration</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Review active LLM provider, database connections, and tool allowlists.</div>',
        unsafe_allow_html=True,
    )

    ready_data = fetch_api("/health/ready")
    st.markdown("#### Subsystem Status")
    st.json(ready_data)

    st.markdown("#### Active Guardrails")
    st.markdown("- **Max Plan Steps:** 6")
    st.markdown("- **Max Tool Retries:** 2")
    st.markdown("- **Max Validation Retries:** 2")
    st.markdown("- **Authorized Tools Allowlist:** `['calculator', 'web_search', 'url_fetch']`")
    st.markdown("- **Mathematical Engine:** AST Parser (Strictly Sandboxed, zero `eval()`)")
