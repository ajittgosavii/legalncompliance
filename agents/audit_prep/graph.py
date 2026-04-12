"""
Audit Analysis & Preparation - LangGraph Multi-Agent
Supervisor pattern: Supervisor → Evidence Collector + Gap Analyzer + Response Drafter
"""

import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_claude_sonnet
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


# --- Simulated Evidence Repository ---
SAMPLE_EVIDENCE = {
    "wildfire": [
        {"doc_id": "WMP-2025", "title": "2025 Wildfire Mitigation Plan", "type": "plan", "status": "current", "location": "SharePoint/Compliance/WMP/"},
        {"doc_id": "VEG-RPT-Q4", "title": "Q4 2025 Vegetation Management Report", "type": "report", "status": "current", "location": "SharePoint/Compliance/Vegetation/"},
        {"doc_id": "PSPS-PROC-V3", "title": "PSPS Protocol v3.2", "type": "procedure", "status": "current", "location": "SharePoint/Operations/PSPS/"},
        {"doc_id": "CAM-DEPLOY", "title": "HD Camera Deployment Tracker", "type": "tracker", "status": "partial", "location": "SharePoint/IT/Monitoring/"},
    ],
    "cybersecurity": [
        {"doc_id": "CIP-ASSESS-2025", "title": "NERC CIP Annual Assessment 2025", "type": "assessment", "status": "current", "location": "SharePoint/IT/NERC-CIP/"},
        {"doc_id": "ESP-INVENTORY", "title": "Electronic Security Perimeter Inventory", "type": "inventory", "status": "current", "location": "SharePoint/IT/Security/"},
        {"doc_id": "VULN-SCAN-Q4", "title": "Q4 Vulnerability Scan Results", "type": "report", "status": "current", "location": "SharePoint/IT/Security/Scans/"},
    ],
    "environmental": [
        {"doc_id": "GHG-RPT-2025", "title": "2025 GHG Emissions Report", "type": "report", "status": "current", "location": "SharePoint/Environmental/GHG/"},
        {"doc_id": "CAP-TRADE-COMP", "title": "Cap-and-Trade Compliance Filing", "type": "filing", "status": "current", "location": "SharePoint/Environmental/CapTrade/"},
    ],
    "grid_reliability": [
        {"doc_id": "TPL-STUDY-2025", "title": "2025 Transmission Planning Study", "type": "study", "status": "current", "location": "SharePoint/Planning/Transmission/"},
        {"doc_id": "CONTINGENCY-ANALYSIS", "title": "N-1-1 Contingency Analysis Report", "type": "analysis", "status": "needs_update", "location": "SharePoint/Planning/Reliability/"},
    ],
}


def plan_audit(state: AuditState) -> AuditState:
    """Supervisor: Plan the audit preparation approach."""
    llm = get_claude_sonnet()

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
    llm = get_claude_sonnet()

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
    llm = get_claude_sonnet()

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
    llm = get_claude_sonnet()

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
    llm = get_claude_sonnet()

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
    "strengths": ["areas where PG&E is well-prepared"],
    "weaknesses": ["areas of concern"],
    "recommendations": ["prioritized list of actions before audit"],
    "timeline_assessment": "whether PG&E can be ready by audit date"
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
