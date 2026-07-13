"""
Page 2: Obligation Impact Analysis
Agentic AI — 4-node LangGraph with deep scoring
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


st.set_page_config(page_title="Obligation Impact | Regulatory Compliance AI", page_icon="📊", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_pipeline, render_empty_state, severity_badge)
from core.ui import bootstrap, require_llm, render_review_gate

inject_styles()
pack = bootstrap()

render_page_header(
    title="Obligation Impact Analysis",
    description="Decomposes regulations into atomic obligations, cross-references existing requirements, scores multi-dimensional impact, and generates executive reports",
    ai_type="agentic"
)

render_pipeline(["Decompose Obligations", "Cross-Reference", "Score Impact", "Executive Report"])

# --- Input ---
render_section("Select Regulation to Analyze")

REGULATIONS = pack["regulations"]

selected_reg = st.selectbox(
    "Regulation",
    options=[f"[{u['source']}] {u['title']}" for u in REGULATIONS],
    index=0,
    label_visibility="collapsed",
)

selected_idx = next(i for i, u in enumerate(REGULATIONS)
                    if f"[{u['source']}] {u['title']}" == selected_reg)
selected_data = REGULATIONS[selected_idx]

with st.expander("View Full Regulation Text", expanded=False):
    st.text(selected_data["text"])

col1, col2 = st.columns([4, 1])
with col2:
    analyze_button = st.button("Run Impact Analysis", type="primary", use_container_width=True)

st.markdown("---")

if analyze_button:
    require_llm()

    from agents.obligation_impact.graph import run_obligation_impact

    with st.status("Running 4-step impact analysis...", expanded=True) as status_ui:
        st.write("Step 1/4: Decomposing into atomic obligations...")
        st.write("Step 2/4: Cross-referencing existing requirements...")
        st.write("Step 3/4: Scoring multi-dimensional impact...")
        st.write("Step 4/4: Generating executive report...")
        result = run_obligation_impact(
            regulation_text=selected_data["text"],
            regulation_source=f"{selected_data['source']}: {selected_data['title']}"
        )
        status_ui.update(label="Impact analysis complete!", state="complete", expanded=False)

    report = result.get("report", {})
    obligations = result.get("atomic_obligations", [])
    scores = result.get("impact_scores", [])

    render_review_gate()

    # --- Executive Report ---
    if report:
        render_section("Executive Report")

        total_obs = report.get("total_obligations", len(obligations))
        critical_obs = report.get("critical_obligations", "N/A")
        low = report.get("estimated_total_cost_low", 0)
        high = report.get("estimated_total_cost_high", 0)

        if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > 0:
            cost_str = f"${low/1e6:.0f}M - ${high/1e6:.0f}M"
        else:
            cost_str = f"{low} - {high}"

        render_kpi_row([
            {"value": str(total_obs), "label": "Total Obligations"},
            {"value": str(critical_obs), "label": "Critical Obligations"},
            {"value": cost_str, "label": "Estimated Cost Range"},
            {"value": str(report.get("earliest_deadline", "N/A")), "label": "Earliest Deadline"},
        ])

        st.markdown(f"> **Executive Summary**: {report.get('executive_summary', 'N/A')}")

        if report.get("key_risks"):
            st.warning("**Key Risks**\n" + "\n".join(f"- {r}" for r in report["key_risks"]))

        if report.get("recommended_actions"):
            render_section("Recommended Actions")
            table_html = '<table class="data-table"><tr><th>Priority</th><th>Action</th><th>Owner</th><th>Deadline</th></tr>'
            for action in report["recommended_actions"]:
                if isinstance(action, dict):
                    pri = action.get('priority', 'N/A').upper()
                    table_html += f"<tr><td><strong>{pri}</strong></td><td>{action.get('action', 'N/A')}</td><td>{action.get('owner', 'N/A')}</td><td>{action.get('deadline', 'TBD')}</td></tr>"
                else:
                    table_html += f"<tr><td>-</td><td colspan='3'>{action}</td></tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

        if report.get("board_attention_items"):
            st.error("**Board Attention Required**\n" + "\n".join(f"- {item}" for item in report["board_attention_items"]))

    # --- Obligations Detail ---
    render_section("Decomposed Obligations", f"{len(obligations)} atomic obligations identified")

    score_map = {s.get("ob_id", ""): s for s in scores}

    for ob in obligations:
        ob_id = ob.get("ob_id", "N/A")
        score = score_map.get(ob_id, {})
        priority = score.get("overall_priority", "medium")
        icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "🟢"}.get(priority, "⚪")

        with st.expander(f"{icon} {ob_id}: {ob.get('obligation', 'N/A')[:100]}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Category**: `{ob.get('category', 'N/A')}`")
                st.markdown(f"**Deadline**: `{ob.get('deadline', 'TBD')}`")
            with c2:
                st.markdown(f"**Entity**: {ob.get('obligated_entity', 'N/A')}")
                st.markdown(f"**Measurement**: {ob.get('measurement_criteria', 'N/A')}")
            with c3:
                st.markdown(f"**Priority**: {severity_badge(priority)}", unsafe_allow_html=True)
                if score.get("recommended_approach"):
                    st.markdown(f"**Approach**: {score['recommended_approach']}")

            if score:
                sc1, sc2, sc3, sc4 = st.columns(4)
                for col, key, label in [(sc1, "cost_impact", "Cost"), (sc2, "operational_impact", "Operations"),
                                         (sc3, "timeline_risk", "Timeline"), (sc4, "penalty_risk", "Penalty")]:
                    with col:
                        sub = score.get(key, {})
                        if isinstance(sub, dict):
                            val = sub.get("score", "?")
                            st.metric(label, f"{val}/10")

    # Cross-References
    cross_refs = result.get("cross_references", [])
    if cross_refs:
        render_section("Cross-Reference Analysis")
        for ref in cross_refs:
            conflicts = ref.get("conflicts_with", [])
            overlaps = ref.get("overlaps_with", [])
            if conflicts or overlaps:
                with st.expander(f"**{ref.get('ob_id', 'N/A')}** — {len(conflicts)} conflict(s), {len(overlaps)} overlap(s)"):
                    if conflicts:
                        st.warning(f"**Conflicts with**: {', '.join(conflicts)}\n\n**Resolution**: {ref.get('resolution_approach', 'N/A')}")
                    if overlaps:
                        st.info(f"**Overlaps with**: {', '.join(overlaps)}")
                    if ref.get("synergies"):
                        st.success(f"**Synergies**: {ref['synergies']}")

    with st.expander("View Raw Agent Output (JSON)"):
        st.json(result)

else:
    render_empty_state(
        icon="📊",
        title="Select a Regulation to Analyze",
        description="Choose a regulation from the dropdown above and click 'Run Impact Analysis' to start the 4-step agentic pipeline"
    )
