"""
Page 1: Regulatory Change Monitor
Agentic AI — 5-node LangGraph pipeline
"""

import streamlit as st
import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Regulatory Monitor | PWE Compliance AI", page_icon="📡", layout="wide")

st.markdown("""
<style>
    .severity-critical { background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 12px; font-weight: 600; }
    .severity-high { background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 12px; font-weight: 600; }
    .severity-medium { background: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 12px; font-weight: 600; }
    .severity-low { background: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 12px; font-weight: 600; }
    .step-active { color: #2563eb; font-weight: bold; }
    .step-done { color: #059669; }
    .step-pending { color: #9ca3af; }
</style>
""", unsafe_allow_html=True)

st.title("📡 Regulatory Change Monitor")
st.markdown("**Agentic AI** — Multi-step pipeline that fetches, classifies, extracts obligations, and generates alerts.")

# --- Controls ---
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    source_filter = st.selectbox(
        "Regulatory Source",
        ["all", "CPUC", "FERC", "NERC", "CARB", "EPA"],
        help="Filter to a specific regulatory body or monitor all sources"
    )
with col2:
    st.markdown("")
    st.markdown("")
    st.markdown(f"**Pipeline**: Fetch → Classify → Extract → Map → Alert")
with col3:
    run_button = st.button("🚀 Run Monitor Agent", type="primary", use_container_width=True)

st.markdown("---")

if run_button:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set. Please configure it in your .env file or environment variables.")
        st.code("export ANTHROPIC_API_KEY='your-key-here'")
        st.stop()

    # --- Progress Tracking ---
    progress_container = st.container()
    with progress_container:
        steps = ["Fetching regulatory updates", "Classifying changes with AI", "Extracting obligations", "Mapping to PWE departments", "Generating alerts"]
        progress_bar = st.progress(0)
        status_text = st.empty()

    try:
        from agents.regulatory_monitor.graph import run_regulatory_monitor

        # Show step-by-step progress
        for i, step in enumerate(steps):
            status_text.markdown(f"**Step {i+1}/5**: {step}...")
            progress_bar.progress((i + 1) / 5)
            if i == 0:
                # Actually run the full pipeline
                result = run_regulatory_monitor(source_filter=source_filter)

        progress_bar.progress(1.0)
        status_text.markdown("**Pipeline complete!**")

        # --- Display Results ---
        alerts = result.get("alerts", [])
        obligations = result.get("extracted_obligations", [])
        mappings = result.get("impact_mappings", [])

        # Summary metrics
        st.subheader("Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Regulatory Updates", len(result.get("raw_updates", [])))
        with m2:
            st.metric("Obligations Extracted", len(obligations))
        with m3:
            critical = sum(1 for a in alerts if a.get("severity") == "critical")
            st.metric("Critical Alerts", critical)
        with m4:
            depts = set()
            for m in mappings:
                depts.add(m.get("primary_department", ""))
                depts.update(m.get("supporting_departments", []))
            st.metric("Departments Affected", len(depts))

        st.markdown("---")

        # --- Alert Cards ---
        st.subheader("Regulatory Alerts")
        for alert in alerts:
            severity = alert.get("severity", "medium")
            severity_class = f"severity-{severity}"

            with st.expander(
                f"{'🔴' if severity == 'critical' else '🟡' if severity == 'high' else '🔵' if severity == 'medium' else '🟢'} "
                f"[{alert.get('source', '')}] {alert.get('title', 'Unknown')}",
                expanded=(severity in ["critical", "high"])
            ):
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    st.markdown(f"**Severity**: <span class='{severity_class}'>{severity.upper()}</span>", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"**Type**: {alert.get('change_type', 'N/A')}")
                with col_c:
                    st.markdown(f"**Obligations**: {alert.get('obligation_count', 0)}")

                st.markdown(f"**Summary**: {alert.get('summary', 'N/A')}")

                deadlines = alert.get("key_deadlines", [])
                if deadlines:
                    st.markdown(f"**Key Deadlines**: {', '.join(deadlines)}")

                if alert.get("penalty_info"):
                    st.warning(f"**Penalty Risk**: {alert['penalty_info']}")

                if alert.get("affected_departments"):
                    st.markdown(f"**Affected Departments**: {', '.join(alert['affected_departments'])}")

                # Obligations detail
                obs = alert.get("obligations", [])
                if obs:
                    st.markdown("**Extracted Obligations:**")
                    for ob in obs:
                        st.markdown(f"- `{ob.get('obligation_id', 'N/A')}`: {ob.get('description', 'N/A')} "
                                    f"(Deadline: {ob.get('deadline', 'TBD')})")

                # Impact mappings
                alert_mappings = alert.get("impact_mappings", [])
                if alert_mappings:
                    st.markdown("**Department Impact Mapping:**")
                    for m in alert_mappings:
                        st.markdown(f"- **{m.get('primary_department', 'N/A')}**: "
                                    f"{m.get('operational_impact', 'N/A')} "
                                    f"(Effort: {m.get('estimated_effort', 'N/A')}, "
                                    f"Timeline: {m.get('timeline_risk', 'N/A')})")

        # --- Raw Data ---
        with st.expander("View Raw Agent Output (JSON)"):
            st.json(result)

    except Exception as e:
        st.error(f"Agent execution failed: {str(e)}")
        st.exception(e)

else:
    # --- Demo / Preview Mode ---
    st.info("Click **Run Monitor Agent** to execute the 5-step agentic pipeline against live regulatory data.")

    st.subheader("Monitored Sources")
    from agents.regulatory_monitor.tools import SAMPLE_REGULATORY_UPDATES

    for update in SAMPLE_REGULATORY_UPDATES:
        with st.expander(f"[{update['source']}] {update['title']} — {update['published_date']}"):
            st.markdown(update['text'][:500] + "...")
            st.caption(f"Source: {update['url']}")

    st.markdown("---")
    st.subheader("Agent Pipeline Architecture")
    st.markdown("""
    ```
    ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
    │  FETCH   │───▶│ CLASSIFY │───▶│  EXTRACT  │───▶│   MAP    │───▶│  ALERT   │
    │ Sources  │    │ (Claude) │    │ Obligations│    │ to Depts │    │ Generate │
    │          │    │          │    │ (Claude)   │    │ (Claude) │    │          │
    └──────────┘    └──────────┘    └───────────┘    └──────────┘    └──────────┘
         5               4              3→N             N→M            Sorted
      sources        classifications   obligations    mappings       by severity
    ```
    """)
