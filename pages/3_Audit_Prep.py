"""
Page 3: Audit Analysis & Preparation
Agentic AI — Supervisor + 3 Sub-Agent pattern
"""

import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Audit Preparation | PG&E Compliance AI", page_icon="📋", layout="wide")

st.title("📋 Audit Analysis & Preparation")
st.markdown("**Agentic AI** — Supervisor agent coordinates Evidence Collector, Gap Analyzer, and Response Drafter to produce audit-ready packages.")

# --- Audit Configuration ---
st.subheader("Configure Audit Scope")

col1, col2 = st.columns(2)
with col1:
    audit_scope = st.selectbox(
        "Audit Type",
        ["CPUC Wildfire Safety Audit", "NERC CIP Cybersecurity Audit",
         "CARB Emissions Compliance Audit", "FERC Transmission Planning Review",
         "Custom Audit Scope"],
    )

    if audit_scope == "Custom Audit Scope":
        audit_scope = st.text_input("Enter custom audit scope")

with col2:
    regulations = st.multiselect(
        "Regulations in Scope",
        ["CPUC Wildfire Mitigation Plan", "CPUC General Order 95", "CPUC General Order 165",
         "NERC CIP-002 to CIP-014", "NERC CIP-015-1 (New)",
         "CARB Cap-and-Trade Regulation", "CARB MRR",
         "FERC Order 901 (New)", "FERC Form 714",
         "CPUC AI Governance (Proposed)"],
        default=["CPUC Wildfire Mitigation Plan", "CPUC General Order 165"]
    )

# Sample obligations for the selected audit type
AUDIT_OBLIGATIONS = {
    "CPUC Wildfire Safety Audit": [
        {"id": "WF-001", "text": "Semi-annual vegetation inspection in Tier 3 HFTDs", "category": "vegetation", "deadline": "2026-06-30"},
        {"id": "WF-002", "text": "Underground 300 circuit-miles in HFTDs", "category": "grid_hardening", "deadline": "2027-12-31"},
        {"id": "WF-003", "text": "50% reduction in PSPS events vs 2024 baseline", "category": "psps", "deadline": "2026-12-31"},
        {"id": "WF-004", "text": "Deploy HD cameras at 100% of Tier 3 transmission structures", "category": "monitoring", "deadline": "2026-06-30"},
        {"id": "WF-005", "text": "Quarterly compliance reports within 30 days of quarter end", "category": "reporting", "deadline": "Ongoing"},
    ],
    "NERC CIP Cybersecurity Audit": [
        {"id": "CIP-001", "text": "Network security monitoring for high/medium impact BES Cyber Systems", "category": "monitoring", "deadline": "2027-10-01"},
        {"id": "CIP-002", "text": "90-day network data retention", "category": "data_retention", "deadline": "2027-10-01"},
        {"id": "CIP-003", "text": "Quarterly anomaly detection baseline updates", "category": "detection", "deadline": "Ongoing"},
        {"id": "CIP-004", "text": "95% ESP network traffic monitoring coverage", "category": "coverage", "deadline": "2027-10-01"},
    ],
    "CARB Emissions Compliance Audit": [
        {"id": "EM-001", "text": "Monthly GHG emissions reporting (enhanced from quarterly)", "category": "reporting", "deadline": "2026-07-01"},
        {"id": "EM-002", "text": "Methane leak detection protocol implementation", "category": "monitoring", "deadline": "2026-07-01"},
        {"id": "EM-003", "text": "Allowance proceeds ratepayer benefit demonstration", "category": "financial", "deadline": "2026-12-31"},
    ],
}

obligations = AUDIT_OBLIGATIONS.get(audit_scope, AUDIT_OBLIGATIONS["CPUC Wildfire Safety Audit"])

st.markdown("**Obligations in Scope:**")
for ob in obligations:
    st.markdown(f"- `{ob['id']}`: {ob['text']} (Deadline: {ob['deadline']})")

col_run, _ = st.columns([1, 3])
with col_run:
    run_audit = st.button("🤖 Run Audit Prep Agent", type="primary", use_container_width=True)

st.markdown("---")

if run_audit:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set.")
        st.stop()

    from agents.audit_prep.graph import run_audit_preparation

    progress = st.progress(0)
    status = st.empty()

    steps = ["Supervisor planning audit approach",
             "Evidence Collector gathering documents",
             "Gap Analyzer identifying compliance gaps",
             "Response Drafter preparing responses",
             "Supervisor reviewing final package"]

    for i, step in enumerate(steps):
        status.markdown(f"**Agent {i+1}/5**: {step}...")
        progress.progress((i + 1) / 5)
        if i == 0:
            result = run_audit_preparation(
                audit_scope=audit_scope,
                regulations=regulations,
                obligations=obligations
            )

    progress.progress(1.0)
    status.markdown("**Audit preparation complete!**")

    # --- Supervisor Review ---
    review = result.get("supervisor_review", {})
    if review:
        st.subheader("Supervisor Assessment")

        r1, r2 = st.columns([1, 3])
        with r1:
            readiness = review.get("overall_readiness", "unknown")
            score = review.get("readiness_score", 0)
            color = {"ready": "green", "mostly_ready": "orange", "significant_gaps": "red", "not_ready": "red"}.get(readiness, "gray")
            st.metric("Readiness Score", f"{score}/100")
            st.markdown(f"**Status**: :{color}[{readiness.replace('_', ' ').title()}]")

        with r2:
            st.markdown(f"**Executive Summary**: {review.get('executive_summary', 'N/A')}")

        if review.get("critical_items"):
            st.error("**Critical Items Requiring Immediate Attention:**\n" +
                     "\n".join(f"- {item}" for item in review["critical_items"]))

        col_s, col_w = st.columns(2)
        with col_s:
            if review.get("strengths"):
                st.success("**Strengths**\n" + "\n".join(f"- {s}" for s in review["strengths"]))
        with col_w:
            if review.get("weaknesses"):
                st.warning("**Weaknesses**\n" + "\n".join(f"- {w}" for w in review["weaknesses"]))

        if review.get("recommendations"):
            st.subheader("Recommendations")
            for rec in review["recommendations"]:
                st.markdown(f"- {rec}")

    # --- Evidence Inventory ---
    st.markdown("---")
    st.subheader("Evidence Inventory")

    evidence = result.get("evidence_inventory", [])
    for ev in evidence:
        status_icon = {"complete": "✅", "partial": "⚠️", "missing": "❌", "error": "💥"}.get(
            ev.get("evidence_status", ""), "❓"
        )
        with st.expander(f"{status_icon} {ev.get('obligation_id', 'N/A')}: {ev.get('obligation_summary', 'N/A')[:80]}"):
            st.markdown(f"**Evidence Status**: {ev.get('evidence_status', 'N/A').upper()}")

            found = ev.get("evidence_found", [])
            if found:
                st.markdown("**Evidence Found:**")
                for f in found:
                    st.markdown(f"  - `{f.get('doc_id', 'N/A')}`: Relevance={f.get('relevance', 'N/A')}, "
                                f"Sufficiency={f.get('sufficiency', 'N/A')}")

            missing = ev.get("missing_evidence", [])
            if missing:
                st.warning("**Missing Evidence:**\n" + "\n".join(f"- {m}" for m in missing))

    # --- Gap Analysis ---
    st.markdown("---")
    st.subheader("Gap Analysis")

    gaps = result.get("gap_analysis", [])
    if gaps:
        for gap in gaps:
            sev = gap.get("severity", "medium")
            icon = {"critical": "🔴", "high": "🟡", "medium": "🔵", "low": "🟢"}.get(sev, "⚪")
            with st.expander(f"{icon} {gap.get('gap_id', 'N/A')}: {gap.get('description', 'N/A')[:80]}"):
                st.markdown(f"**Type**: {gap.get('gap_type', 'N/A')} | **Severity**: {sev.upper()}")
                st.markdown(f"**Obligation**: {gap.get('obligation_id', 'N/A')}")
                st.markdown(f"**Audit Risk**: {gap.get('audit_risk', 'N/A')}")
                remediation = gap.get("remediation", {})
                if isinstance(remediation, dict):
                    st.markdown(f"**Remediation**: {remediation.get('action', 'N/A')} "
                                f"(Owner: {remediation.get('owner', 'N/A')}, Effort: {remediation.get('effort', 'N/A')})")
                if gap.get("interim_mitigation"):
                    st.info(f"**Interim Mitigation**: {gap['interim_mitigation']}")
    else:
        st.success("No significant gaps identified.")

    # --- Draft Responses ---
    st.markdown("---")
    st.subheader("Draft Audit Responses")

    responses = result.get("draft_responses", [])
    for resp in responses:
        compliance = resp.get("compliance_status", "unknown")
        icon = {"full": "✅", "substantial": "🟡", "partial": "⚠️", "non_compliant": "❌"}.get(compliance, "❓")
        with st.expander(f"{icon} {resp.get('area', 'N/A')} — {compliance.replace('_', ' ').title()}"):
            st.markdown(resp.get("response_narrative", "N/A"))
            citations = resp.get("evidence_citations", [])
            if citations:
                st.markdown("**Evidence Cited**: " + ", ".join(f"`{c}`" for c in citations))

            corrective = resp.get("corrective_actions", [])
            if corrective:
                st.markdown("**Corrective Actions:**")
                for ca in corrective:
                    if isinstance(ca, dict):
                        st.markdown(f"- [{ca.get('status', 'planned').upper()}] {ca.get('action', 'N/A')} "
                                    f"(Owner: {ca.get('owner', 'N/A')}, Target: {ca.get('target_date', 'TBD')})")

    # Raw output
    with st.expander("View Raw Agent Output (JSON)"):
        st.json(result)

else:
    st.info("Configure audit scope and click **Run Audit Prep Agent** to start the multi-agent workflow.")

    st.subheader("Multi-Agent Architecture")
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────┐
    │                   SUPERVISOR AGENT                       │
    │          (Plans, coordinates, reviews)                   │
    │                                                          │
    │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
    │  │  Evidence   │  │  Gap        │  │  Response        │  │
    │  │  Collector  │  │  Analyzer   │  │  Drafter         │  │
    │  │             │  │             │  │                  │  │
    │  │ Searches    │  │ Compares    │  │ Drafts formal    │  │
    │  │ doc repos   │  │ evidence    │  │ audit responses  │  │
    │  │ Validates   │  │ vs reqs    │  │ with citations   │  │
    │  └─────────────┘  └─────────────┘  └──────────────────┘  │
    └─────────────────────────────────────────────────────────┘
    ```
    """)
