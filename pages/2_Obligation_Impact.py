"""
Page 2: Obligation Impact Analysis
Agentic AI — 4-node LangGraph with Opus for deep scoring
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load API keys from Streamlit secrets
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(page_title="Obligation Impact | PWE Compliance AI", page_icon="📊", layout="wide")

st.title("📊 Obligation Impact Analysis")
st.markdown("**Agentic AI** — Decomposes regulations, cross-references existing obligations, scores multi-dimensional impact, generates executive reports.")

# --- Input Section ---
st.subheader("Input Regulation")

# Pre-loaded sample regulations
from agents.regulatory_monitor.tools import SAMPLE_REGULATORY_UPDATES

selected_reg = st.selectbox(
    "Select a regulation to analyze",
    options=[u["title"] for u in SAMPLE_REGULATORY_UPDATES],
    index=0
)

selected_data = next(u for u in SAMPLE_REGULATORY_UPDATES if u["title"] == selected_reg)

with st.expander("View Full Regulation Text", expanded=False):
    st.text(selected_data["text"])

col1, col2 = st.columns([3, 1])
with col2:
    analyze_button = st.button("🧠 Run Impact Analysis", type="primary", use_container_width=True)

st.markdown("---")

if analyze_button:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set. Please configure in .env or environment.")
        st.stop()

    from agents.obligation_impact.graph import run_obligation_impact

    progress = st.progress(0)
    status = st.empty()

    steps = ["Decomposing into atomic obligations", "Cross-referencing existing requirements",
             "Scoring impact (Claude Opus)", "Generating executive report"]

    for i, step in enumerate(steps):
        status.markdown(f"**Step {i+1}/4**: {step}...")
        progress.progress((i + 1) / 4)
        if i == 0:
            result = run_obligation_impact(
                regulation_text=selected_data["text"],
                regulation_source=f"{selected_data['source']}: {selected_data['title']}"
            )

    progress.progress(1.0)
    status.markdown("**Analysis complete!**")

    # --- Executive Report ---
    report = result.get("report", {})
    if report:
        st.subheader("Executive Report")

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Total Obligations", report.get("total_obligations", len(result.get("atomic_obligations", []))))
        with r2:
            st.metric("Critical Obligations", report.get("critical_obligations", "N/A"))
        with r3:
            low = report.get("estimated_total_cost_low", "N/A")
            high = report.get("estimated_total_cost_high", "N/A")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                st.metric("Est. Cost Range", f"${low/1e6:.1f}M - ${high/1e6:.1f}M")
            else:
                st.metric("Est. Cost Range", f"{low} - {high}")
        with r4:
            st.metric("Earliest Deadline", report.get("earliest_deadline", "N/A"))

        st.markdown(f"**Executive Summary**: {report.get('executive_summary', 'N/A')}")

        if report.get("key_risks"):
            st.warning("**Key Risks**\n" + "\n".join(f"- {r}" for r in report["key_risks"]))

        if report.get("recommended_actions"):
            st.subheader("Recommended Actions")
            for action in report["recommended_actions"]:
                if isinstance(action, dict):
                    st.markdown(f"- **[{action.get('priority', 'N/A').upper()}]** {action.get('action', 'N/A')} "
                                f"— Owner: {action.get('owner', 'N/A')} | Deadline: {action.get('deadline', 'TBD')}")
                else:
                    st.markdown(f"- {action}")

        if report.get("board_attention_items"):
            st.error("**Board Attention Required**\n" + "\n".join(f"- {item}" for item in report["board_attention_items"]))

    # --- Obligations Detail ---
    st.markdown("---")
    st.subheader("Decomposed Obligations")

    obligations = result.get("atomic_obligations", [])
    scores = result.get("impact_scores", [])

    # Create a lookup for scores
    score_map = {s.get("ob_id", ""): s for s in scores}

    for ob in obligations:
        ob_id = ob.get("ob_id", "N/A")
        score = score_map.get(ob_id, {})
        priority = score.get("overall_priority", "medium")

        icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "🟢"}.get(priority, "⚪")

        with st.expander(f"{icon} {ob_id}: {ob.get('obligation', 'N/A')[:100]}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Category**: {ob.get('category', 'N/A')}")
                st.markdown(f"**Deadline**: {ob.get('deadline', 'TBD')}")
            with c2:
                st.markdown(f"**Entity**: {ob.get('obligated_entity', 'N/A')}")
                st.markdown(f"**Measurement**: {ob.get('measurement_criteria', 'N/A')}")
            with c3:
                st.markdown(f"**Priority**: {priority.upper()}")
                if score.get("recommended_approach"):
                    st.markdown(f"**Approach**: {score['recommended_approach']}")

            if score:
                st.markdown("**Impact Scores:**")
                sc1, sc2, sc3, sc4 = st.columns(4)
                for col, key, label in [(sc1, "cost_impact", "Cost"), (sc2, "operational_impact", "Operations"),
                                         (sc3, "timeline_risk", "Timeline"), (sc4, "penalty_risk", "Penalty")]:
                    with col:
                        sub = score.get(key, {})
                        if isinstance(sub, dict):
                            val = sub.get("score", "?")
                            st.metric(label, f"{val}/10")

    # --- Cross-References ---
    cross_refs = result.get("cross_references", [])
    if cross_refs:
        st.markdown("---")
        st.subheader("Cross-Reference Analysis")
        for ref in cross_refs:
            conflicts = ref.get("conflicts_with", [])
            overlaps = ref.get("overlaps_with", [])
            if conflicts or overlaps:
                st.markdown(f"**{ref.get('ob_id', 'N/A')}**")
                if conflicts:
                    st.warning(f"Conflicts with: {', '.join(conflicts)}")
                    st.markdown(f"Resolution: {ref.get('resolution_approach', 'N/A')}")
                if overlaps:
                    st.info(f"Overlaps with: {', '.join(overlaps)}")
                if ref.get("synergies"):
                    st.success(f"Synergies: {ref['synergies']}")

    # --- Raw Output ---
    with st.expander("View Raw Agent Output (JSON)"):
        st.json(result)

else:
    st.info("Select a regulation and click **Run Impact Analysis** to start the 4-step agentic pipeline.")

    st.subheader("Agent Pipeline Architecture")
    st.markdown("""
    ```
    ┌────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
    │ DECOMPOSE  │───▶│ CROSS-REF   │───▶│    SCORE     │───▶│   REPORT     │
    │ Atomic     │    │ vs Existing │    │ Multi-Dim    │    │  Executive   │
    │ Obligations│    │ Obligations │    │ (Opus 4.6)   │    │  Summary     │
    └────────────┘    └─────────────┘    └──────────────┘    └──────────────┘
       Sonnet            Sonnet              Opus               Sonnet
    ```
    """)
