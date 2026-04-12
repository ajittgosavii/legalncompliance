"""
Page 4: Case Analytics
Gen AI — RAG-powered historical case analysis
"""

import streamlit as st
import json
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(page_title="Case Analytics | PWE Compliance AI", page_icon="🔍", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_empty_state, severity_badge, source_badge)

inject_styles()

render_page_header(
    title="Case Analytics",
    description="Semantic search and AI analysis over historical enforcement cases, penalties, and regulatory precedents across 7 regulatory bodies",
    ai_type="genai"
)

# --- Data ---
from agents.case_analytics.chain import SAMPLE_CASES, PENALTY_TIMELINE, get_case_stats, run_case_analytics

stats = get_case_stats()

# --- KPIs ---
render_kpi_row([
    {"value": str(stats["total_cases"]), "label": "Total Cases", "sublabel": "Across 7 regulators"},
    {"value": f"${stats['total_penalties']/1e9:.1f}B", "label": "Total Penalties"},
    {"value": f"${stats['average_penalty']/1e6:.0f}M", "label": "Average Penalty"},
    {"value": f"${stats['max_penalty']/1e9:.1f}B", "label": "Largest Penalty", "sublabel": "Camp Fire 2018"},
    {"value": str(stats["penalty_cases"]), "label": "Penalty Cases"},
])

# --- Charts ---
render_section("Penalty Trends & Analytics")

# Timeline chart
timeline_df = pd.DataFrame(PENALTY_TIMELINE)
timeline_by_year = timeline_df.groupby(["year", "regulator"]).agg(
    total=("total_penalties", "sum"), cases=("case_count", "sum")
).reset_index()

fig_timeline = px.bar(
    timeline_by_year, x="year", y="total", color="regulator",
    title="Annual Penalties by Regulator",
    labels={"total": "Penalty Amount ($)", "year": "Year"},
    color_discrete_map={"CPUC": "#6d28d9", "NERC/FERC": "#1d4ed8", "CARB": "#059669",
                        "PHMSA": "#dc2626", "Cal-OSHA": "#d97706", "CEC": "#0891b2"},
    barmode="stack"
)
fig_timeline.update_layout(
    xaxis=dict(dtick=1), yaxis_title="Penalty Amount ($)",
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter, sans-serif"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_timeline, use_container_width=True)

col_c1, col_c2 = st.columns(2)

with col_c1:
    reg_data = pd.DataFrame(list(stats["by_regulator"].items()), columns=["Regulator", "Count"])
    fig_reg = px.pie(reg_data, values="Count", names="Regulator", title="Cases by Regulator",
                     color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
    fig_reg.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Inter"))
    st.plotly_chart(fig_reg, use_container_width=True)

with col_c2:
    penalty_cases = sorted([c for c in SAMPLE_CASES if c["penalty_amount"] > 0],
                           key=lambda x: x["penalty_amount"], reverse=True)[:10]
    if penalty_cases:
        pdf = pd.DataFrame(penalty_cases)
        pdf["penalty_m"] = pdf["penalty_amount"] / 1e6
        pdf["short_title"] = pdf["case_title"].str[:40] + "..."
        fig_top = px.bar(pdf, y="short_title", x="penalty_m", color="regulator",
                         title="Top 10 Penalties ($M)", orientation="h",
                         color_discrete_map={"CPUC": "#6d28d9", "NERC/FERC": "#1d4ed8",
                                             "CARB": "#059669", "PHMSA": "#dc2626", "Cal-OSHA": "#d97706"})
        fig_top.update_layout(yaxis_title="", xaxis_title="Penalty ($M)",
                              plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Inter"),
                              showlegend=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# --- AI Search ---
render_section("AI-Powered Case Analysis", "Ask questions about enforcement history, penalties, or compliance risks")

col_q1, col_q2 = st.columns([4, 1])
with col_q1:
    query = st.text_input(
        "Search",
        placeholder="e.g., What are the precedents for wildfire-related penalties?",
        label_visibility="collapsed"
    )
with col_q2:
    analysis_type = st.selectbox("Type", ["precedent", "trend", "risk", "summary"], label_visibility="collapsed")

# Quick queries
qc1, qc2, qc3, qc4 = st.columns(4)
with qc1:
    if st.button("Wildfire penalties", use_container_width=True):
        query = "What are the precedents and penalties for wildfire-related enforcement?"
        analysis_type = "precedent"
with qc2:
    if st.button("Cybersecurity risk", use_container_width=True):
        query = "What is PWE's exposure to NERC CIP cybersecurity enforcement?"
        analysis_type = "risk"
with qc3:
    if st.button("Penalty trends", use_container_width=True):
        query = "How have regulatory penalties trended over time?"
        analysis_type = "trend"
with qc4:
    if st.button("Pipeline safety", use_container_width=True):
        query = "What enforcement actions relate to pipeline safety and PHMSA?"
        analysis_type = "precedent"

if query:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        st.error("OPENAI_API_KEY not set. Please configure in Streamlit Cloud Secrets.")
        st.stop()

    with st.status(f"Running {analysis_type} analysis...", expanded=True) as status_ui:
        st.write("Searching case database...")
        st.write("Analyzing with GPT-4o...")
        result = run_case_analytics(query=query, analysis_type=analysis_type)
        status_ui.update(label="Analysis complete!", state="complete", expanded=False)

    render_section("Analysis Results")
    st.markdown(result.get("executive_summary", "No summary available."))

    relevant = result.get("relevant_cases", [])
    if relevant:
        render_section("Relevant Cases")
        for case in relevant:
            if isinstance(case, dict):
                st.markdown(f"- **{case.get('case_number', 'N/A')}**: {case.get('relevance', 'N/A')}")
                st.caption(f"Takeaway: {case.get('key_takeaway', 'N/A')}")

    risk = result.get("risk_assessment", {})
    if isinstance(risk, dict) and risk.get("overall_risk"):
        render_section("Risk Assessment")
        rc1, rc2 = st.columns(2)
        with rc1:
            overall = risk.get("overall_risk", "unknown")
            st.markdown(f"**Overall Risk**: {severity_badge(overall)}", unsafe_allow_html=True)
            if risk.get("estimated_penalty_exposure"):
                st.metric("Penalty Exposure", risk["estimated_penalty_exposure"])
        with rc2:
            if risk.get("highest_risk_areas"):
                for area in risk["highest_risk_areas"]:
                    st.markdown(f"- {area}")

    recs = result.get("recommendations", [])
    if recs:
        render_section("Recommendations")
        for r in recs:
            st.markdown(f"- {r}")

    with st.expander("View Raw Analysis (JSON)"):
        st.json(result)

# --- Case Browser ---
st.markdown("---")
render_section("Case Browser", f"{len(SAMPLE_CASES)} cases across {len(stats['by_regulator'])} regulators")

# Filters
fc1, fc2, fc3 = st.columns(3)
with fc1:
    filter_reg = st.selectbox("Filter by Regulator", ["All"] + list(stats["by_regulator"].keys()), key="browse_reg")
with fc2:
    filter_type = st.selectbox("Filter by Type", ["All"] + list(stats["by_type"].keys()), key="browse_type")
with fc3:
    filter_penalty = st.selectbox("Filter by Penalty", ["All", "With Penalty", "No Penalty"], key="browse_pen")

filtered = SAMPLE_CASES
if filter_reg != "All":
    filtered = [c for c in filtered if c["regulator"] == filter_reg]
if filter_type != "All":
    filtered = [c for c in filtered if c["case_type"] == filter_type]
if filter_penalty == "With Penalty":
    filtered = [c for c in filtered if c["penalty_amount"] > 0]
elif filter_penalty == "No Penalty":
    filtered = [c for c in filtered if c["penalty_amount"] == 0]

st.caption(f"Showing {len(filtered)} of {len(SAMPLE_CASES)} cases")

for case in filtered:
    penalty_str = f"${case['penalty_amount']:,.0f}" if case['penalty_amount'] > 0 else "—"
    icon = "🟢" if case["status"] == "resolved" else "🔵"

    with st.expander(f"{icon} {case['case_number']} — {case['case_title'][:70]}"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Regulator**: {source_badge(case['regulator'])}", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Type**: `{case['case_type']}`")
        with c3:
            st.markdown(f"**Status**: `{case['status']}`")
        with c4:
            st.markdown(f"**Penalty**: **{penalty_str}**")

        st.markdown(f"**Filed**: {case['filing_date']} | **Resolved**: {case.get('resolution_date') or 'Ongoing'}")
        st.markdown(f"> {case['summary']}")
        st.markdown(f"**Key Findings**: {case['key_findings']}")
        st.markdown(f"**Tags**: `{case['precedent_tags']}`")
