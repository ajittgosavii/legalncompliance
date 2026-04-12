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

st.set_page_config(page_title="Case Analytics | PG&E Compliance AI", page_icon="🔍", layout="wide")

st.title("🔍 Case Analytics")
st.markdown("**Gen AI (RAG)** — Semantic search and AI analysis over historical CPUC/FERC enforcement cases, penalties, and precedents.")

# --- Load Case Data ---
from agents.case_analytics.chain import SAMPLE_CASES, get_case_stats, run_case_analytics

stats = get_case_stats()

# --- Dashboard Overview ---
st.subheader("Enforcement Case Dashboard")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Cases", stats["total_cases"])
with m2:
    st.metric("Total Penalties", f"${stats['total_penalties']/1e9:.2f}B")
with m3:
    st.metric("Avg Penalty", f"${stats['average_penalty']/1e6:.1f}M")
with m4:
    st.metric("Cases with Penalties", stats["penalty_cases"])

st.markdown("---")

# --- Visualizations ---
col_v1, col_v2 = st.columns(2)

with col_v1:
    # Cases by regulator
    reg_data = pd.DataFrame(list(stats["by_regulator"].items()), columns=["Regulator", "Count"])
    fig_reg = px.pie(reg_data, values="Count", names="Regulator", title="Cases by Regulator",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_reg, use_container_width=True)

with col_v2:
    # Cases by type
    type_data = pd.DataFrame(list(stats["by_type"].items()), columns=["Type", "Count"])
    fig_type = px.bar(type_data, x="Type", y="Count", title="Cases by Type",
                      color="Type", color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_type, use_container_width=True)

# Penalty distribution
penalty_cases = [c for c in SAMPLE_CASES if c["penalty_amount"] > 0]
if penalty_cases:
    penalty_df = pd.DataFrame(penalty_cases)
    penalty_df["penalty_millions"] = penalty_df["penalty_amount"] / 1e6
    fig_pen = px.bar(penalty_df, x="case_number", y="penalty_millions",
                     title="Penalty Amounts by Case ($M)",
                     color="regulator",
                     hover_data=["case_title"],
                     color_discrete_sequence=px.colors.qualitative.Bold)
    fig_pen.update_layout(xaxis_title="Case Number", yaxis_title="Penalty ($M)")
    st.plotly_chart(fig_pen, use_container_width=True)

st.markdown("---")

# --- Case Search & AI Analysis ---
st.subheader("AI-Powered Case Analysis")

col_q1, col_q2 = st.columns([3, 1])
with col_q1:
    query = st.text_input(
        "Ask about enforcement cases, penalties, or compliance risks",
        placeholder="e.g., What are the precedents for wildfire-related penalties?",
        value=""
    )
with col_q2:
    analysis_type = st.selectbox(
        "Analysis Type",
        ["precedent", "trend", "risk", "summary"]
    )

# Quick query suggestions
st.markdown("**Quick queries:**")
qc1, qc2, qc3, qc4 = st.columns(4)
with qc1:
    if st.button("Wildfire penalties", use_container_width=True):
        query = "What are the precedents and penalties for wildfire-related enforcement actions?"
        analysis_type = "precedent"
with qc2:
    if st.button("Cybersecurity risk", use_container_width=True):
        query = "What is PG&E's exposure to NERC CIP cybersecurity enforcement?"
        analysis_type = "risk"
with qc3:
    if st.button("Penalty trends", use_container_width=True):
        query = "How have regulatory penalties trended over time for California utilities?"
        analysis_type = "trend"
with qc4:
    if st.button("Environmental cases", use_container_width=True):
        query = "What enforcement actions relate to emissions and environmental compliance?"
        analysis_type = "precedent"

if query:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set.")
        st.stop()

    with st.spinner(f"Running {analysis_type} analysis..."):
        result = run_case_analytics(query=query, analysis_type=analysis_type)

    # Executive Summary
    st.subheader("Analysis Results")
    st.markdown(result.get("executive_summary", "No summary available."))

    # Relevant Cases
    relevant = result.get("relevant_cases", [])
    if relevant:
        st.subheader("Relevant Cases")
        for case in relevant:
            if isinstance(case, dict):
                st.markdown(f"- **{case.get('case_number', 'N/A')}**: {case.get('relevance', 'N/A')}")
                st.markdown(f"  *Key Takeaway*: {case.get('key_takeaway', 'N/A')}")

    # Risk Assessment
    risk = result.get("risk_assessment", {})
    if isinstance(risk, dict) and risk:
        st.subheader("Risk Assessment")
        risk_col1, risk_col2 = st.columns(2)
        with risk_col1:
            overall = risk.get("overall_risk", "unknown")
            color = {"low": "green", "medium": "orange", "high": "red", "critical": "red"}.get(overall, "gray")
            st.markdown(f"**Overall Risk**: :{color}[{overall.upper()}]")
            if risk.get("estimated_penalty_exposure"):
                st.markdown(f"**Estimated Penalty Exposure**: {risk['estimated_penalty_exposure']}")
        with risk_col2:
            if risk.get("highest_risk_areas"):
                st.markdown("**Highest Risk Areas:**")
                for area in risk["highest_risk_areas"]:
                    st.markdown(f"- {area}")

    # Patterns
    patterns = result.get("patterns_identified", [])
    if patterns:
        st.subheader("Patterns Identified")
        for p in patterns:
            st.markdown(f"- {p}")

    # Recommendations
    recs = result.get("recommendations", [])
    if recs:
        st.subheader("Recommendations")
        for r in recs:
            st.markdown(f"- {r}")

    with st.expander("View Raw Analysis (JSON)"):
        st.json(result)

# --- Case Browser ---
st.markdown("---")
st.subheader("Case Browser")

for case in SAMPLE_CASES:
    penalty_str = f"${case['penalty_amount']:,.0f}" if case['penalty_amount'] > 0 else "No penalty"
    status_icon = "🟢" if case["status"] == "resolved" else "🔵"

    with st.expander(f"{status_icon} {case['case_number']} — {case['case_title'][:70]}"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Regulator**: {case['regulator']}")
        with c2:
            st.markdown(f"**Type**: {case['case_type']}")
        with c3:
            st.markdown(f"**Status**: {case['status']}")
        with c4:
            st.markdown(f"**Penalty**: {penalty_str}")

        st.markdown(f"**Filed**: {case['filing_date']} | **Resolved**: {case.get('resolution_date', 'Ongoing')}")
        st.markdown(f"**Summary**: {case['summary']}")
        st.markdown(f"**Key Findings**: {case['key_findings']}")
        st.markdown(f"**Tags**: `{case['precedent_tags']}`")
