"""
Page 1: Regulatory Change Monitor
Agentic AI — 5-node LangGraph pipeline
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load API keys from Streamlit secrets
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(page_title="Regulatory Monitor | Regulatory Compliance AI", page_icon="📡", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_pipeline, render_empty_state,
                          severity_badge, source_badge)

inject_styles()

render_page_header(
    title="Regulatory Change Monitor",
    description="Multi-step agentic pipeline that fetches, classifies, extracts obligations, maps to departments, and generates prioritized alerts",
    ai_type="agentic"
)

# --- Pipeline Visualization ---
render_pipeline(["Fetch Sources", "Classify Changes", "Extract Obligations", "Map to Depts", "Generate Alerts"])

# --- Controls ---
st.markdown("")
col1, col2, col3 = st.columns([2, 4, 2])
with col1:
    source_filter = st.selectbox(
        "Filter by Regulator",
        ["all", "CPUC", "FERC", "NERC", "CARB", "EPA", "PHMSA", "Cal-OSHA"],
        help="Monitor a specific regulatory body or all sources"
    )
with col3:
    st.markdown("")
    run_button = st.button("Run Monitor Agent", type="primary", use_container_width=True)

st.markdown("---")

if run_button:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        st.error("OPENAI_API_KEY not set. Please configure it in Streamlit Cloud Secrets (Settings > Secrets).")
        st.stop()

    try:
        from agents.regulatory_monitor.graph import run_regulatory_monitor

        with st.status("Running 5-step agentic pipeline...", expanded=True) as status_ui:
            st.write("Step 1/5: Fetching regulatory updates...")
            st.write("Step 2/5: Classifying changes with AI...")
            st.write("Step 3/5: Extracting obligations...")
            st.write("Step 4/5: Mapping to Company departments...")
            st.write("Step 5/5: Generating prioritized alerts...")
            result = run_regulatory_monitor(source_filter=source_filter)
            status_ui.update(label="Pipeline complete!", state="complete", expanded=False)

        alerts = result.get("alerts", [])
        obligations = result.get("extracted_obligations", [])
        mappings = result.get("impact_mappings", [])

        # Summary KPIs
        critical = sum(1 for a in alerts if a.get("severity") == "critical")
        high = sum(1 for a in alerts if a.get("severity") == "high")
        depts = set()
        for m in mappings:
            depts.add(m.get("primary_department", ""))
            depts.update(m.get("supporting_departments", []))

        render_kpi_row([
            {"value": str(len(result.get("raw_updates", []))), "label": "Regulations Scanned"},
            {"value": str(len(obligations)), "label": "Obligations Extracted"},
            {"value": str(critical), "label": "Critical Alerts", "sublabel": f"+ {high} High Priority"},
            {"value": str(len(depts)), "label": "Departments Affected"},
        ])

        # --- Alert Cards ---
        render_section("Regulatory Alerts", "Sorted by severity — critical items require immediate attention")

        for alert in alerts:
            severity = alert.get("severity", "medium")
            with st.expander(
                f"{'🔴' if severity == 'critical' else '🟡' if severity == 'high' else '🔵' if severity == 'medium' else '🟢'} "
                f"[{alert.get('source', '')}] {alert.get('title', 'Unknown')}",
                expanded=(severity in ["critical", "high"])
            ):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"**Severity**: {severity_badge(severity)}", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**Source**: {source_badge(alert.get('source', 'N/A'))}", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"**Type**: `{alert.get('change_type', 'N/A')}`")
                with c4:
                    st.markdown(f"**Obligations**: `{alert.get('obligation_count', 0)}`")

                st.markdown(f"> {alert.get('summary', 'N/A')}")

                deadlines = alert.get("key_deadlines", [])
                if deadlines:
                    st.warning(f"**Key Deadlines**: {', '.join(deadlines)}")

                if alert.get("penalty_info"):
                    st.error(f"**Penalty Risk**: {alert['penalty_info']}")

                if alert.get("affected_departments"):
                    st.info(f"**Affected Departments**: {', '.join(alert['affected_departments'])}")

                # Obligations table
                obs = alert.get("obligations", [])
                if obs:
                    render_section("Extracted Obligations")
                    table_html = '<table class="data-table"><tr><th>ID</th><th>Description</th><th>Deadline</th><th>Category</th></tr>'
                    for ob in obs:
                        table_html += f"<tr><td><code>{ob.get('obligation_id', 'N/A')}</code></td><td>{ob.get('description', 'N/A')[:120]}</td><td>{ob.get('deadline', 'TBD')}</td><td>{ob.get('category', 'N/A')}</td></tr>"
                    table_html += "</table>"
                    st.markdown(table_html, unsafe_allow_html=True)

        with st.expander("View Raw Agent Output (JSON)"):
            st.json(result)

    except Exception as e:
        st.error(f"Agent execution failed: {str(e)}")
        st.exception(e)

else:
    # --- Preview Mode ---
    render_section("Monitored Regulatory Sources", "12 active regulations across 7 regulatory bodies — click Run Monitor Agent to analyze")

    from agents.regulatory_monitor.tools import SAMPLE_REGULATORY_UPDATES

    # Group by source
    sources = {}
    for u in SAMPLE_REGULATORY_UPDATES:
        sources.setdefault(u["source"], []).append(u)

    for source, updates in sources.items():
        with st.expander(f"{source_badge(source)} — {len(updates)} regulation(s)", expanded=False):
            for u in updates:
                st.markdown(f"**{u['title']}**")
                st.caption(f"Published: {u['published_date']}")
                st.markdown(u['text'][:300] + "...")
                st.markdown("---")

    render_empty_state(
        icon="📡",
        title="Ready to Monitor",
        description="Click 'Run Monitor Agent' to execute the 5-step agentic pipeline and generate regulatory alerts"
    )
