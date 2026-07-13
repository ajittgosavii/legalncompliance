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

st.set_page_config(page_title="Regulatory Monitor | Regulatory Compliance AI", page_icon="📡", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_pipeline, render_empty_state,
                          severity_badge, source_badge)
from core.ui import bootstrap, require_llm, render_review_gate, render_data_provenance, citation_badge

inject_styles()
pack = bootstrap()

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
        ["all"] + [r["code"] for r in pack["regulators"]],
        help="Monitor a specific regulatory body or all sources",
    )
with col3:
    st.markdown("")
    run_button = st.button("Run Monitor Agent", type="primary", use_container_width=True)

st.markdown("---")

if run_button:
    require_llm()

    try:
        from agents.regulatory_monitor.graph import run_regulatory_monitor

        with st.status("Running 5-step agentic pipeline...", expanded=True) as status_ui:
            st.write("Step 1/5: Fetching regulatory updates...")
            st.write("Step 2/5: Classifying changes with AI...")
            st.write("Step 3/5: Extracting obligations...")
            st.write("Step 4/5: Mapping to departments...")
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

        verified = sum(1 for o in obligations if o.get("citation_verified"))
        unverified = len(obligations) - verified

        render_kpi_row([
            {"value": str(len(result.get("raw_updates", []))), "label": "Regulations Scanned"},
            {"value": str(len(obligations)), "label": "Obligations Extracted"},
            {"value": f"{verified}/{len(obligations)}" if obligations else "0/0",
             "label": "Citations Verified",
             "sublabel": f"{unverified} need manual check" if unverified else "all traced to source"},
            {"value": str(critical), "label": "Critical Alerts", "sublabel": f"+ {high} High Priority"},
            {"value": str(len(depts)), "label": "Departments Affected"},
        ])

        render_review_gate()
        if unverified:
            st.warning(
                f"**{unverified} obligation(s) could not be traced to a verbatim quote in the source text.** "
                "They are shown with a warning badge and downgraded confidence. Verify them against the "
                "source before entering them into any compliance register."
            )

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
                    render_section("Extracted Obligations", "Each obligation is traced back to the source text")
                    for ob in obs:
                        st.markdown(
                            f"**`{ob.get('obligation_id', 'N/A')}`** &nbsp; {citation_badge(ob)}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(ob.get("description", "N/A"))
                        oc1, oc2, oc3 = st.columns(3)
                        with oc1:
                            st.caption(f"**Deadline**: {ob.get('deadline', 'not stated in source')}")
                        with oc2:
                            st.caption(f"**Category**: {ob.get('category', 'N/A')}")
                        with oc3:
                            st.caption(f"**Confidence**: {ob.get('confidence', 'N/A')}")
                        quote = ob.get("source_quote")
                        if quote:
                            st.markdown(
                                f'<div class="source-quote">"{quote}"<br>'
                                f'<span style="font-style:normal;font-size:0.75rem;color:#64748b;">'
                                f'&mdash; {ob.get("source_section", "source")}, {ob.get("source_body", "")}</span></div>',
                                unsafe_allow_html=True,
                            )
                        st.markdown("---")

        with st.expander("View Raw Agent Output (JSON)"):
            st.json(result)

    except Exception as e:
        st.error(f"Agent execution failed: {str(e)}")
        st.exception(e)

else:
    # --- Preview Mode ---
    render_section(
        "Monitored Regulatory Sources",
        f"{len(pack['regulations'])} regulations across {len(pack['regulators'])} regulatory bodies "
        f"({pack['label']}) \u2014 click Run Monitor Agent to analyze",
    )
    render_data_provenance()

    sources = {}
    for u in pack["regulations"]:
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
