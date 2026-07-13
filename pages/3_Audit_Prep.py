"""
Page 3: Audit Analysis & Preparation
Agentic AI — Supervisor + 3 Sub-Agent pattern
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


st.set_page_config(page_title="Audit Preparation | Regulatory Compliance AI", page_icon="📋", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_pipeline, render_empty_state,
                          severity_badge, status_badge)
from core.ui import bootstrap, require_llm, render_review_gate, render_data_provenance

inject_styles()
pack = bootstrap()

render_page_header(
    title="Audit Analysis & Preparation",
    description="Multi-agent system with Supervisor coordinating Evidence Collector, Gap Analyzer, and Response Drafter to produce audit-ready packages",
    ai_type="agentic"
)

render_pipeline(["Supervisor Plans", "Collect Evidence", "Analyze Gaps", "Draft Responses", "Supervisor Review"])

# --- Configuration ---
render_section("Configure Audit Scope")

AUDIT_TYPES = pack["audit_types"]

col1, col2 = st.columns(2)
with col1:
    audit_scope = st.selectbox(
        "Audit Type",
        list(AUDIT_TYPES),
        help=f"Audit types defined for {pack['label']}",
    )

with col2:
    regulations = st.multiselect(
        "Regulations in Scope",
        pack["existing_obligations"] + [u["title"] for u in pack["regulations"]],
        default=pack["existing_obligations"][:2],
    )

obligations = AUDIT_TYPES[audit_scope]
# Obligations table
table_html = '<table class="data-table"><tr><th>ID</th><th>Obligation</th><th>Category</th><th>Deadline</th></tr>'
for ob in obligations:
    table_html += f"<tr><td><code>{ob['id']}</code></td><td>{ob['text']}</td><td>{ob['category']}</td><td>{ob['deadline']}</td></tr>"
table_html += "</table>"
st.markdown(table_html, unsafe_allow_html=True)

col_run, _ = st.columns([1, 4])
with col_run:
    run_audit = st.button("Run Audit Prep Agent", type="primary", use_container_width=True)

st.markdown("---")

if run_audit:
    require_llm()

    from agents.audit_prep.graph import run_audit_preparation

    with st.status("Running multi-agent audit preparation...", expanded=True) as status_ui:
        st.write("Supervisor: Planning audit approach...")
        st.write("Evidence Collector: Gathering documents...")
        st.write("Gap Analyzer: Identifying compliance gaps...")
        st.write("Response Drafter: Preparing responses...")
        st.write("Supervisor: Reviewing final package...")
        result = run_audit_preparation(audit_scope=audit_scope, regulations=regulations, obligations=obligations)
        status_ui.update(label="Audit preparation complete!", state="complete", expanded=False)

    render_review_gate()

    # --- Supervisor Review ---
    review = result.get("supervisor_review", {})
    if review:
        render_section("Supervisor Assessment")

        score = review.get("readiness_score", 0)
        readiness = review.get("overall_readiness", "unknown")

        r1, r2 = st.columns([1, 3])
        with r1:
            gauge_cls = "gauge-ready" if score >= 80 else "gauge-mostly" if score >= 60 else "gauge-gaps"
            st.markdown(f"""
            <div class="readiness-gauge">
                <div class="gauge-value {gauge_cls}">{score}</div>
                <div class="gauge-label">Readiness Score</div>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"**Overall Readiness**: {status_badge(readiness.replace('_', ' '))}", unsafe_allow_html=True)
            st.markdown(f"> {review.get('executive_summary', 'N/A')}")

        if review.get("critical_items"):
            st.error("**Critical Items**\n" + "\n".join(f"- {item}" for item in review["critical_items"]))

        c_s, c_w = st.columns(2)
        with c_s:
            if review.get("strengths"):
                st.success("**Strengths**\n" + "\n".join(f"- {s}" for s in review["strengths"]))
        with c_w:
            if review.get("weaknesses"):
                st.warning("**Weaknesses**\n" + "\n".join(f"- {w}" for w in review["weaknesses"]))

    # --- Evidence ---
    evidence = result.get("evidence_inventory", [])
    if evidence:
        render_section("Evidence Inventory", f"{len(evidence)} obligation(s) assessed")
        for ev in evidence:
            icon = {"complete": "✅", "partial": "⚠️", "missing": "❌"}.get(ev.get("evidence_status", ""), "❓")
            with st.expander(f"{icon} {ev.get('obligation_id', 'N/A')}: {ev.get('obligation_summary', 'N/A')[:80]}"):
                st.markdown(f"**Status**: {status_badge(ev.get('evidence_status', 'unknown'))}", unsafe_allow_html=True)
                found = ev.get("evidence_found", [])
                if found:
                    for f in found:
                        st.markdown(f"- `{f.get('doc_id', '')}` — Relevance: {f.get('relevance', 'N/A')}, Sufficiency: {f.get('sufficiency', 'N/A')}")
                missing = ev.get("missing_evidence", [])
                if missing:
                    st.warning("**Missing**: " + "; ".join(missing))

    # --- Gaps ---
    gaps = result.get("gap_analysis", [])
    if gaps:
        render_section("Gap Analysis", f"{len(gaps)} gap(s) identified")
        for gap in gaps:
            sev = gap.get("severity", "medium")
            icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "🟢"}.get(sev, "⚪")
            with st.expander(f"{icon} {gap.get('gap_id', 'N/A')}: {gap.get('description', 'N/A')[:80]}"):
                st.markdown(f"**Severity**: {severity_badge(sev)} | **Type**: `{gap.get('gap_type', 'N/A')}`", unsafe_allow_html=True)
                remediation = gap.get("remediation", {})
                if isinstance(remediation, dict):
                    st.info(f"**Remediation**: {remediation.get('action', 'N/A')} — Owner: {remediation.get('owner', 'N/A')}, Effort: {remediation.get('effort', 'N/A')}")

    # --- Responses ---
    responses = result.get("draft_responses", [])
    if responses:
        render_section("Draft Audit Responses")
        for resp in responses:
            compliance = resp.get("compliance_status", "unknown")
            icon = {"full": "✅", "substantial": "🟡", "partial": "⚠️", "non_compliant": "❌"}.get(compliance, "❓")
            with st.expander(f"{icon} {resp.get('area', 'N/A')} — {compliance.replace('_', ' ').title()}"):
                st.markdown(resp.get("response_narrative", "N/A"))
                citations = resp.get("evidence_citations", [])
                if citations:
                    st.markdown("**Evidence Cited**: " + ", ".join(f"`{c}`" for c in citations))

    with st.expander("View Raw Agent Output (JSON)"):
        st.json(result)

else:
    render_data_provenance()
    render_empty_state(
        icon="📋",
        title="Configure and Run Audit Preparation",
        description="Select an audit type, choose regulations in scope, then click 'Run Audit Prep Agent' to start the multi-agent workflow"
    )
