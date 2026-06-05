"""
Audit Analysis & Preparation - LangGraph Multi-Agent
Supervisor pattern: Supervisor → Evidence Collector + Gap Analyzer + Response Drafter
"""

import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import (
    AUDIT_SUPERVISOR_PROMPT,
    AUDIT_EVIDENCE_PROMPT,
    AUDIT_GAP_PROMPT,
    AUDIT_RESPONSE_PROMPT,
)


class AuditState(TypedDict):
    audit_scope: str
    regulations: list[str]
    obligations: list[dict]
    evidence_inventory: list[dict]
    gap_analysis: list[dict]
    draft_responses: list[dict]
    supervisor_review: dict
    final_package: dict
    current_step: str
    iteration: int


# --- Simulated Evidence Repository (35+ documents across 8 categories) ---
SAMPLE_EVIDENCE = {
    "wildfire": [
        {"doc_id": "WMP-2025", "title": "2025 Wildfire Mitigation Plan", "type": "plan", "status": "current", "location": "SharePoint/Compliance/WMP/", "last_updated": "2025-03-15", "owner": "Wildfire Safety"},
        {"doc_id": "WMP-2026-DRAFT", "title": "2026 WMP Draft — For CPUC Review", "type": "plan", "status": "draft", "location": "SharePoint/Compliance/WMP/2026/", "last_updated": "2026-01-20", "owner": "Wildfire Safety"},
        {"doc_id": "VEG-RPT-Q4", "title": "Q4 2025 Vegetation Management Report", "type": "report", "status": "current", "location": "SharePoint/Compliance/Vegetation/", "last_updated": "2026-01-10", "owner": "Vegetation Mgmt"},
        {"doc_id": "VEG-RPT-Q1-2026", "title": "Q1 2026 Vegetation Management Report", "type": "report", "status": "current", "location": "SharePoint/Compliance/Vegetation/", "last_updated": "2026-04-08", "owner": "Vegetation Mgmt"},
        {"doc_id": "VEG-INSPECT-TRACKER", "title": "Tier 3 HFTD Vegetation Inspection Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Compliance/Vegetation/Inspections/", "last_updated": "2026-04-01", "owner": "Vegetation Mgmt"},
        {"doc_id": "PSPS-PROC-V3", "title": "PSPS Protocol v3.2", "type": "procedure", "status": "current", "location": "SharePoint/Operations/PSPS/", "last_updated": "2025-09-22", "owner": "Electric Operations"},
        {"doc_id": "PSPS-EVENT-LOG-2025", "title": "2025 PSPS Event Log and Impact Analysis", "type": "report", "status": "current", "location": "SharePoint/Operations/PSPS/Events/", "last_updated": "2026-01-15", "owner": "Electric Operations"},
        {"doc_id": "CAM-DEPLOY", "title": "HD Camera Deployment Tracker", "type": "tracker", "status": "partial", "location": "SharePoint/IT/Monitoring/", "last_updated": "2026-03-01", "owner": "IT Operations"},
        {"doc_id": "WEATHER-STATION-INV", "title": "Weather Station Network Inventory", "type": "inventory", "status": "current", "location": "SharePoint/IT/Monitoring/Weather/", "last_updated": "2025-12-15", "owner": "Meteorology"},
        {"doc_id": "COVERED-CONDUCTOR-RPT", "title": "Covered Conductor Installation Progress Report", "type": "report", "status": "current", "location": "SharePoint/Engineering/Grid-Hardening/", "last_updated": "2026-03-15", "owner": "Engineering"},
        {"doc_id": "UNDERGROUND-TRACKER", "title": "10,000 Mile Undergrounding Program Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Engineering/Undergrounding/", "last_updated": "2026-04-01", "owner": "Engineering"},
    ],
    "cybersecurity": [
        {"doc_id": "CIP-ASSESS-2025", "title": "NERC CIP Annual Assessment 2025", "type": "assessment", "status": "current", "location": "SharePoint/IT/NERC-CIP/", "last_updated": "2025-12-20", "owner": "Cybersecurity"},
        {"doc_id": "ESP-INVENTORY", "title": "Electronic Security Perimeter Inventory", "type": "inventory", "status": "current", "location": "SharePoint/IT/Security/", "last_updated": "2026-01-30", "owner": "Cybersecurity"},
        {"doc_id": "VULN-SCAN-Q4", "title": "Q4 2025 Vulnerability Scan Results", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Scans/", "last_updated": "2026-01-05", "owner": "Cybersecurity"},
        {"doc_id": "VULN-SCAN-Q1-2026", "title": "Q1 2026 Vulnerability Scan Results", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Scans/", "last_updated": "2026-04-03", "owner": "Cybersecurity"},
        {"doc_id": "PATCH-MGMT-LOG", "title": "BES Cyber Asset Patch Management Log", "type": "log", "status": "current", "location": "SharePoint/IT/Security/Patches/", "last_updated": "2026-03-28", "owner": "Cybersecurity"},
        {"doc_id": "IRP-V4", "title": "Incident Response Plan v4.1", "type": "procedure", "status": "current", "location": "SharePoint/IT/Security/IR/", "last_updated": "2025-11-15", "owner": "Cybersecurity"},
        {"doc_id": "SEC-TRAINING-2025", "title": "2025 CIP Security Training Completion Report", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Training/", "last_updated": "2026-01-10", "owner": "HR/Cybersecurity"},
        {"doc_id": "ACCESS-REVIEW-Q1", "title": "Q1 2026 Access Control Review — BES Systems", "type": "review", "status": "current", "location": "SharePoint/IT/Security/Access/", "last_updated": "2026-04-05", "owner": "Cybersecurity"},
        {"doc_id": "NETWORK-MONITOR-GAPS", "title": "Network Monitoring Coverage Gap Analysis", "type": "analysis", "status": "needs_update", "location": "SharePoint/IT/Security/Monitoring/", "last_updated": "2025-06-20", "owner": "Cybersecurity"},
    ],
    "environmental": [
        {"doc_id": "GHG-RPT-2025", "title": "2025 Annual GHG Emissions Report", "type": "report", "status": "current", "location": "SharePoint/Environmental/GHG/", "last_updated": "2026-03-01", "owner": "Environmental"},
        {"doc_id": "CAP-TRADE-COMP", "title": "Cap-and-Trade Compliance Period 4 Filing", "type": "filing", "status": "current", "location": "SharePoint/Environmental/CapTrade/", "last_updated": "2025-11-01", "owner": "Environmental"},
        {"doc_id": "METHANE-LDAR-RPT", "title": "Methane LDAR Survey Results — Gas Distribution", "type": "report", "status": "current", "location": "SharePoint/Environmental/Methane/", "last_updated": "2026-02-15", "owner": "Gas Operations"},
        {"doc_id": "SF6-INVENTORY", "title": "SF6 Switchgear Inventory and Emissions Log", "type": "inventory", "status": "needs_update", "location": "SharePoint/Environmental/SF6/", "last_updated": "2025-04-30", "owner": "Electric Operations"},
        {"doc_id": "EPA-SUBPART-W", "title": "EPA Subpart W Annual Report — GHG Reporting", "type": "filing", "status": "current", "location": "SharePoint/Environmental/EPA/", "last_updated": "2026-03-20", "owner": "Environmental"},
        {"doc_id": "CLEAN-ENERGY-PLAN", "title": "Clean Energy Procurement Plan 2025-2030", "type": "plan", "status": "current", "location": "SharePoint/Environmental/CleanEnergy/", "last_updated": "2025-08-15", "owner": "Energy Procurement"},
    ],
    "grid_reliability": [
        {"doc_id": "TPL-STUDY-2025", "title": "2025 Transmission Planning Study", "type": "study", "status": "current", "location": "SharePoint/Planning/Transmission/", "last_updated": "2025-10-30", "owner": "Transmission Planning"},
        {"doc_id": "CONTINGENCY-ANALYSIS", "title": "N-1-1 Contingency Analysis Report", "type": "analysis", "status": "needs_update", "location": "SharePoint/Planning/Reliability/", "last_updated": "2024-11-15", "owner": "Reliability Engineering"},
        {"doc_id": "EXTREME-WEATHER-SCENARIOS", "title": "Extreme Weather Scenario Modeling Results", "type": "study", "status": "partial", "location": "SharePoint/Planning/Weather/", "last_updated": "2026-02-28", "owner": "Transmission Planning"},
        {"doc_id": "FERC-714-FILING", "title": "FERC Form 714 Annual Filing 2025", "type": "filing", "status": "current", "location": "SharePoint/Planning/FERC/", "last_updated": "2026-04-01", "owner": "Regulatory Affairs"},
    ],
    "pipeline_safety": [
        {"doc_id": "DIMP-2025", "title": "Distribution Integrity Management Program 2025", "type": "plan", "status": "current", "location": "SharePoint/Gas/DIMP/", "last_updated": "2025-12-01", "owner": "Gas Operations"},
        {"doc_id": "TIMP-2025", "title": "Transmission Integrity Management Program 2025", "type": "plan", "status": "current", "location": "SharePoint/Gas/TIMP/", "last_updated": "2025-11-15", "owner": "Gas Operations"},
        {"doc_id": "LEAK-SURVEY-RPT-Q4", "title": "Q4 2025 Leak Survey and Repair Report", "type": "report", "status": "current", "location": "SharePoint/Gas/Leaks/", "last_updated": "2026-01-20", "owner": "Gas Operations"},
        {"doc_id": "LEGACY-PIPE-TRACKER", "title": "Cast Iron & Bare Steel Replacement Tracker", "type": "tracker", "status": "current", "location": "SharePoint/Gas/LegacyPipe/", "last_updated": "2026-03-15", "owner": "Gas Engineering"},
        {"doc_id": "ONE-CALL-METRICS", "title": "One-Call Locate & Mark Performance Metrics", "type": "report", "status": "current", "location": "SharePoint/Gas/OneCall/", "last_updated": "2026-04-01", "owner": "Gas Operations"},
        {"doc_id": "MAOP-RECORDS-AUDIT", "title": "MAOP Records Validation Audit Report", "type": "audit", "status": "needs_update", "location": "SharePoint/Gas/MAOP/", "last_updated": "2024-09-30", "owner": "Gas Engineering"},
    ],
    "worker_safety": [
        {"doc_id": "IIPP-2026", "title": "Injury & Illness Prevention Program 2026", "type": "plan", "status": "current", "location": "SharePoint/Safety/IIPP/", "last_updated": "2026-01-05", "owner": "Safety"},
        {"doc_id": "HEAT-ILLNESS-PLAN", "title": "Heat Illness Prevention Plan (Updated)", "type": "procedure", "status": "current", "location": "SharePoint/Safety/Heat/", "last_updated": "2026-03-10", "owner": "Safety"},
        {"doc_id": "WILDFIRE-SMOKE-PROC", "title": "Wildfire Smoke Exposure Protection Procedures", "type": "procedure", "status": "needs_update", "location": "SharePoint/Safety/Smoke/", "last_updated": "2025-05-20", "owner": "Safety"},
        {"doc_id": "LOTO-AUDIT-2025", "title": "2025 Lockout/Tagout Compliance Audit", "type": "audit", "status": "current", "location": "SharePoint/Safety/LOTO/", "last_updated": "2025-12-18", "owner": "Safety"},
        {"doc_id": "CONTRACTOR-SAFETY-RPT", "title": "Contractor Safety Program Verification Report", "type": "report", "status": "current", "location": "SharePoint/Safety/Contractors/", "last_updated": "2026-02-01", "owner": "Safety/Procurement"},
    ],
    "data_privacy": [
        {"doc_id": "PRIVACY-POLICY-V3", "title": "Customer Data Privacy Policy v3.0", "type": "policy", "status": "needs_update", "location": "SharePoint/Legal/Privacy/", "last_updated": "2024-08-15", "owner": "Legal"},
        {"doc_id": "CCPA-COMPLIANCE-RPT", "title": "CCPA/CPRA Annual Compliance Report 2025", "type": "report", "status": "current", "location": "SharePoint/Legal/Privacy/CCPA/", "last_updated": "2026-03-01", "owner": "Legal"},
        {"doc_id": "DATA-SHARING-REGISTRY", "title": "Third-Party Data Sharing Agreement Registry", "type": "registry", "status": "current", "location": "SharePoint/Legal/Privacy/ThirdParty/", "last_updated": "2026-03-15", "owner": "Legal/IT"},
        {"doc_id": "AMI-DATA-CONSENT", "title": "AMI Data Consent Tracking Report", "type": "report", "status": "partial", "location": "SharePoint/Customer/AMI/", "last_updated": "2025-11-30", "owner": "Customer Operations"},
    ],
    "ai_governance": [
        {"doc_id": "AI-POLICY-DRAFT", "title": "AI Governance Policy — Draft", "type": "policy", "status": "draft", "location": "SharePoint/IT/AI/", "last_updated": "2026-02-01", "owner": "IT/Legal"},
        {"doc_id": "AI-INVENTORY", "title": "AI/ML Systems Inventory and Risk Assessment", "type": "inventory", "status": "partial", "location": "SharePoint/IT/AI/Inventory/", "last_updated": "2026-01-15", "owner": "IT"},
        {"doc_id": "AI-BIAS-AUDIT-2025", "title": "2025 AI Bias Audit — Customer Systems", "type": "audit", "status": "current", "location": "SharePoint/IT/AI/Audits/", "last_updated": "2025-12-20", "owner": "IT/Compliance"},
    ],
}


def plan_audit(state: AuditState) -> AuditState:
    """Supervisor: Plan the audit preparation approach."""
    llm = get_openai_primary()

    prompt = f"""As the Audit Preparation Supervisor, plan the audit preparation approach.

AUDIT SCOPE: {state['audit_scope']}
REGULATIONS IN SCOPE: {json.dumps(state['regulations'])}
OBLIGATIONS TO VERIFY: {json.dumps(state['obligations'], indent=2)}

Create an audit preparation plan as JSON:
{{
    "audit_areas": ["categorized list of audit focus areas"],
    "evidence_needed_per_area": {{
        "area_name": ["types of evidence needed"]
    }},
    "priority_order": ["areas ranked by risk/importance"],
    "estimated_preparation_effort": "description",
    "key_risks": ["potential gaps or issues to watch for"]
}}"""

    response = llm.invoke([
        SystemMessage(content=AUDIT_SUPERVISOR_PROMPT),
        HumanMessage(content=prompt)
    ])

    return {**state, "current_step": "collect_evidence"}


def collect_evidence(state: AuditState) -> AuditState:
    """Evidence Collector: Gather and validate evidence for each obligation."""
    llm = get_openai_primary()

    # Combine all available evidence
    all_evidence = []
    for category, docs in SAMPLE_EVIDENCE.items():
        for doc in docs:
            doc["category"] = category
            all_evidence.append(doc)

    prompt = f"""As the Evidence Collector, map available evidence to each obligation.

OBLIGATIONS:
{json.dumps(state['obligations'], indent=2)}

AVAILABLE EVIDENCE INVENTORY:
{json.dumps(all_evidence, indent=2)}

For each obligation, assess evidence coverage:
[
    {{
        "obligation_id": "from the obligations list",
        "obligation_summary": "brief description",
        "evidence_found": [
            {{
                "doc_id": "matching evidence doc ID",
                "relevance": "direct|supporting|partial",
                "sufficiency": "sufficient|partial|insufficient",
                "notes": "any concerns about this evidence"
            }}
        ],
        "evidence_status": "complete|partial|missing",
        "missing_evidence": ["description of what's still needed"],
        "recommended_sources": ["where to find missing evidence"]
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=AUDIT_EVIDENCE_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        evidence = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        evidence = [{"obligation_id": "ALL", "evidence_status": "error", "notes": "Failed to parse evidence mapping"}]

    return {**state, "evidence_inventory": evidence, "current_step": "analyze_gaps"}


def analyze_gaps(state: AuditState) -> AuditState:
    """Gap Analyzer: Identify and prioritize compliance gaps."""
    llm = get_openai_primary()

    prompt = f"""As the Gap Analyzer, identify compliance gaps based on evidence assessment.

OBLIGATIONS:
{json.dumps(state['obligations'], indent=2)}

EVIDENCE INVENTORY:
{json.dumps(state['evidence_inventory'], indent=2)}

For each gap found:
[
    {{
        "gap_id": "unique ID",
        "obligation_id": "related obligation",
        "gap_type": "missing_evidence|outdated_evidence|partial_compliance|process_gap|documentation_gap",
        "description": "clear description of the gap",
        "severity": "critical|high|medium|low",
        "audit_risk": "What could happen if auditor finds this gap",
        "remediation": {{
            "action": "what needs to be done",
            "owner": "responsible department",
            "effort": "hours or days estimate",
            "deadline": "when this must be resolved"
        }},
        "interim_mitigation": "what can be done immediately to reduce risk"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=AUDIT_GAP_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        gaps = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        gaps = []

    return {**state, "gap_analysis": gaps, "current_step": "draft_responses"}


def draft_responses(state: AuditState) -> AuditState:
    """Response Drafter: Prepare professional audit responses."""
    llm = get_openai_primary()

    prompt = f"""As the Response Drafter, prepare professional audit responses.

AUDIT SCOPE: {state['audit_scope']}
OBLIGATIONS: {json.dumps(state['obligations'], indent=2)}
EVIDENCE: {json.dumps(state['evidence_inventory'], indent=2)}
GAPS: {json.dumps(state['gap_analysis'], indent=2)}

Draft responses for each audit area:
[
    {{
        "area": "audit area name",
        "response_narrative": "Professional response text suitable for regulatory submission (2-3 paragraphs)",
        "evidence_citations": ["list of evidence documents cited"],
        "compliance_status": "full|substantial|partial|non_compliant",
        "corrective_actions": [
            {{
                "action": "description",
                "owner": "department",
                "target_date": "date",
                "status": "planned|in_progress|completed"
            }}
        ],
        "risk_mitigation": "how risks are being addressed"
    }}
]"""

    response = llm.invoke([
        SystemMessage(content=AUDIT_RESPONSE_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        responses = json.loads(content[content.find("["):content.rfind("]") + 1])
    except (json.JSONDecodeError, ValueError):
        responses = [{"area": "General", "response_narrative": response.content[:1000], "compliance_status": "unknown"}]

    return {**state, "draft_responses": responses, "current_step": "supervisor_review"}


def supervisor_review(state: AuditState) -> AuditState:
    """Supervisor: Review completeness and quality of audit package."""
    llm = get_openai_primary()

    prompt = f"""As the Audit Supervisor, review the complete audit preparation package.

EVIDENCE COLLECTED: {len(state['evidence_inventory'])} items
GAPS IDENTIFIED: {len(state['gap_analysis'])} gaps
RESPONSES DRAFTED: {len(state['draft_responses'])} areas

EVIDENCE SUMMARY: {json.dumps(state['evidence_inventory'][:5], indent=2)}
GAP SUMMARY: {json.dumps(state['gap_analysis'][:5], indent=2)}
RESPONSE SUMMARY: {json.dumps(state['draft_responses'][:3], indent=2)}

Provide supervisor assessment:
{{
    "overall_readiness": "ready|mostly_ready|significant_gaps|not_ready",
    "readiness_score": 0-100,
    "executive_summary": "2-3 paragraph summary for audit committee",
    "critical_items": ["items requiring immediate executive attention"],
    "strengths": ["areas where the Company is well-prepared"],
    "weaknesses": ["areas of concern"],
    "recommendations": ["prioritized list of actions before audit"],
    "timeline_assessment": "whether the Company can be ready by audit date"
}}"""

    response = llm.invoke([
        SystemMessage(content=AUDIT_SUPERVISOR_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        content = response.content
        review = json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        review = {"overall_readiness": "unknown", "executive_summary": response.content[:500]}

    final_package = {
        "audit_scope": state["audit_scope"],
        "evidence_inventory": state["evidence_inventory"],
        "gap_analysis": state["gap_analysis"],
        "draft_responses": state["draft_responses"],
        "supervisor_review": review,
    }

    return {**state, "supervisor_review": review, "final_package": final_package, "current_step": "complete"}


def build_audit_graph() -> StateGraph:
    """Build the multi-agent audit preparation graph."""
    workflow = StateGraph(AuditState)

    workflow.add_node("plan", plan_audit)
    workflow.add_node("collect_evidence", collect_evidence)
    workflow.add_node("analyze_gaps", analyze_gaps)
    workflow.add_node("draft_responses", draft_responses)
    workflow.add_node("supervisor_review", supervisor_review)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "collect_evidence")
    workflow.add_edge("collect_evidence", "analyze_gaps")
    workflow.add_edge("analyze_gaps", "draft_responses")
    workflow.add_edge("draft_responses", "supervisor_review")
    workflow.add_edge("supervisor_review", END)

    return workflow.compile()


def run_audit_preparation(
    audit_scope: str,
    regulations: list[str],
    obligations: list[dict]
) -> dict:
    """Run full audit preparation workflow."""
    graph = build_audit_graph()

    initial_state: AuditState = {
        "audit_scope": audit_scope,
        "regulations": regulations,
        "obligations": obligations,
        "evidence_inventory": [],
        "gap_analysis": [],
        "draft_responses": [],
        "supervisor_review": {},
        "final_package": {},
        "current_step": "plan",
        "iteration": 0,
    }

    return graph.invoke(initial_state)
