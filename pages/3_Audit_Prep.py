"""
Page 3: Audit Analysis & Preparation
Agentic AI — Supervisor + 3 Sub-Agent pattern
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(page_title="Audit Preparation | Regulatory Compliance AI", page_icon="📋", layout="wide")

from core.styles import (inject_styles, render_page_header, render_kpi_row,
                          render_section, render_pipeline, render_empty_state,
                          severity_badge, status_badge)

inject_styles()

render_page_header(
    title="Audit Analysis & Preparation",
    description="Multi-agent system with Supervisor coordinating Evidence Collector, Gap Analyzer, and Response Drafter to produce audit-ready packages",
    ai_type="agentic"
)

render_pipeline(["Supervisor Plans", "Collect Evidence", "Analyze Gaps", "Draft Responses", "Supervisor Review"])

# --- Configuration ---
render_section("Configure Audit Scope")

col1, col2 = st.columns(2)
with col1:
    audit_scope = st.selectbox(
        "Audit Type",
        ["CPUC Wildfire Safety Audit", "NERC CIP Cybersecurity Audit",
         "CARB Emissions Compliance Audit", "FERC Transmission Planning Review",
         "PHMSA Pipeline Safety Audit", "Cal-OSHA Worker Safety Audit",
         "Customer Data Privacy Audit"],
    )

with col2:
    regulations = st.multiselect(
        "Regulations in Scope",
        ["CPUC Wildfire Mitigation Plan", "CPUC General Order 95", "CPUC General Order 165",
         "NERC CIP-002 to CIP-014", "NERC CIP-015-1 (New)",
         "CARB Cap-and-Trade Regulation", "CARB MRR",
         "FERC Order 901 (New)", "FERC Form 714",
         "PHMSA 49 CFR 192", "Cal-OSHA Title 8",
         "CPUC AI Governance (Proposed)", "CPUC Data Privacy Rules"],
        default=["CPUC Wildfire Mitigation Plan", "CPUC General Order 165"]
    )

# Obligations
AUDIT_OBLIGATIONS = {
    "CPUC Wildfire Safety Audit": [
        {"id": "WF-001", "text": "Semi-annual vegetation inspection in Tier 3 HFTDs", "category": "vegetation", "deadline": "2026-06-30"},
        {"id": "WF-002", "text": "Underground 300 circuit-miles in HFTDs", "category": "grid_hardening", "deadline": "2027-12-31"},
        {"id": "WF-003", "text": "50% reduction in PSPS events vs 2024 baseline", "category": "psps", "deadline": "2026-12-31"},
        {"id": "WF-004", "text": "Deploy HD cameras at 100% of Tier 3 transmission structures", "category": "monitoring", "deadline": "2026-06-30"},
        {"id": "WF-005", "text": "Quarterly compliance reports within 30 days", "category": "reporting", "deadline": "Ongoing"},
        {"id": "WF-006", "text": "Covered conductor on all new Tier 2/3 construction", "category": "grid_hardening", "deadline": "2026-01-01"},
        {"id": "WF-007", "text": "Sectionalizing devices on critical facility circuits", "category": "grid_hardening", "deadline": "2026-12-31"},
        {"id": "WF-008", "text": "AI-powered fire detection system deployment", "category": "technology", "deadline": "2026-06-30"},
    ],
    "NERC CIP Cybersecurity Audit": [
        {"id": "CIP-001", "text": "Network security monitoring for high/medium BES Cyber Systems", "category": "monitoring", "deadline": "2027-10-01"},
        {"id": "CIP-002", "text": "90-day network data retention", "category": "data_retention", "deadline": "2027-10-01"},
        {"id": "CIP-003", "text": "Quarterly anomaly detection baseline updates", "category": "detection", "deadline": "Ongoing"},
        {"id": "CIP-004", "text": "95% ESP network traffic monitoring coverage", "category": "coverage", "deadline": "2027-10-01"},
        {"id": "CIP-005", "text": "Critical security patches within 35 days", "category": "patch_management", "deadline": "Ongoing"},
        {"id": "CIP-006", "text": "Physical Security Perimeter access controls", "category": "physical_security", "deadline": "Ongoing"},
        {"id": "CIP-007", "text": "Annual CIP security training completion", "category": "training", "deadline": "2026-12-31"},
        {"id": "CIP-008", "text": "Low-impact BES electronic access controls", "category": "access_control", "deadline": "2026-06-30"},
    ],
    "CARB Emissions Compliance Audit": [
        {"id": "EM-001", "text": "Monthly GHG emissions reporting", "category": "reporting", "deadline": "2026-07-01"},
        {"id": "EM-002", "text": "Methane leak detection protocol", "category": "monitoring", "deadline": "2026-07-01"},
        {"id": "EM-003", "text": "Allowance proceeds ratepayer benefit", "category": "financial", "deadline": "2026-12-31"},
        {"id": "EM-004", "text": "SF6 switchgear emissions tracking", "category": "reporting", "deadline": "Ongoing"},
        {"id": "EM-005", "text": "EPA Subpart W annual reporting", "category": "reporting", "deadline": "2026-03-31"},
    ],
    "FERC Transmission Planning Review": [
        {"id": "TP-001", "text": "Model 3+ extreme weather scenarios", "category": "planning", "deadline": "2026-06-30"},
        {"id": "TP-002", "text": "Weather-correlated N-1-1 contingency analysis", "category": "reliability", "deadline": "2026-06-30"},
        {"id": "TP-003", "text": "Updated planning criteria filing (Order 901)", "category": "filing", "deadline": "2026-05-20"},
        {"id": "TP-004", "text": "Regional weather assumption coordination", "category": "coordination", "deadline": "2026-06-30"},
    ],
    "PHMSA Pipeline Safety Audit": [
        {"id": "PS-001", "text": "Advanced leak detection (100% system coverage)", "category": "monitoring", "deadline": "2028-01-01"},
        {"id": "PS-002", "text": "Grade 2 leak repair within 6 months", "category": "maintenance", "deadline": "2026-07-01"},
        {"id": "PS-003", "text": "Quarterly methane emissions reports", "category": "reporting", "deadline": "2027-03-31"},
        {"id": "PS-004", "text": "5% annual legacy pipe replacement", "category": "infrastructure", "deadline": "Ongoing"},
        {"id": "PS-005", "text": "GPS-enabled locates, 1-hour emergency response", "category": "operations", "deadline": "2026-12-31"},
    ],
    "Cal-OSHA Worker Safety Audit": [
        {"id": "WS-001", "text": "Heat illness plan — 87°F threshold", "category": "heat_safety", "deadline": "2026-04-01"},
        {"id": "WS-002", "text": "Smoke protection — N95 when AQI >151", "category": "smoke_safety", "deadline": "2026-04-01"},
        {"id": "WS-003", "text": "Contractor safety quarterly verification", "category": "contractor", "deadline": "Ongoing"},
        {"id": "WS-004", "text": "Safety training in primary language", "category": "training", "deadline": "2026-12-31"},
        {"id": "WS-005", "text": "Lockout/tagout compliance", "category": "electrical_safety", "deadline": "Ongoing"},
    ],
    "Customer Data Privacy Audit": [
        {"id": "DP-001", "text": "AMI data explicit opt-in consent", "category": "consent", "deadline": "2026-07-01"},
        {"id": "DP-002", "text": "72-hour breach notification", "category": "breach", "deadline": "2026-07-01"},
        {"id": "DP-003", "text": "Green Button Connect My Data API", "category": "data_access", "deadline": "2026-07-01"},
        {"id": "DP-004", "text": "AI data anonymization (k>=5)", "category": "ai_privacy", "deadline": "2026-07-01"},
    ],
}

obligations = AUDIT_OBLIGATIONS.get(audit_scope, AUDIT_OBLIGATIONS["CPUC Wildfire Safety Audit"])

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
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        st.error("OPENAI_API_KEY not set. Please configure in Streamlit Cloud Secrets.")
        st.stop()

    from agents.audit_prep.graph import run_audit_preparation

    with st.status("Running multi-agent audit preparation...", expanded=True) as status_ui:
        st.write("Supervisor: Planning audit approach...")
        st.write("Evidence Collector: Gathering documents...")
        st.write("Gap Analyzer: Identifying compliance gaps...")
        st.write("Response Drafter: Preparing responses...")
        st.write("Supervisor: Reviewing final package...")
        result = run_audit_preparation(audit_scope=audit_scope, regulations=regulations, obligations=obligations)
        status_ui.update(label="Audit preparation complete!", state="complete", expanded=False)

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
    render_empty_state(
        icon="📋",
        title="Configure and Run Audit Preparation",
        description="Select an audit type, choose regulations in scope, then click 'Run Audit Prep Agent' to start the multi-agent workflow"
    )
